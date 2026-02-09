"""Custom Qwen3 Reranker implementation for LangChain."""
from typing import List, Optional

from langchain_core.documents import Document
from loguru import logger

# Try different import paths for BaseDocumentCompressor (LangChain 1.0+ compatible)
try:
    from langchain_core.retrievers.document_compressors import BaseDocumentCompressor
except ImportError:
    try:
        from langchain_core.retrievers import BaseDocumentCompressor
    except ImportError:
        try:
            from langchain.retrievers.document_compressors import BaseDocumentCompressor
        except ImportError:
            try:
                from langchain.retrievers.document_compressors.base import BaseDocumentCompressor
            except ImportError:
                # Fallback: define a minimal base class if import fails
                from abc import ABC, abstractmethod
                class BaseDocumentCompressor(ABC):
                    @abstractmethod
                    def compress_documents(self, documents, query):
                        """Compress documents based on query."""
                        pass

# Check for required dependencies
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("torch not available, Qwen3 reranker will be disabled")

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers not available, Qwen3 reranker will be disabled")

if not (TORCH_AVAILABLE and TRANSFORMERS_AVAILABLE):
    TRANSFORMERS_AVAILABLE = False


class Qwen3Reranker(BaseDocumentCompressor):
    """Custom reranker using Qwen3-Reranker model via transformers."""

    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-Reranker-0.6B",
        top_n: int = 3,
        instruction: Optional[str] = None,
        max_length: int = 8192,
        use_flash_attention: bool = False,
    ):
        """
        Initialize Qwen3 Reranker.

        Args:
            model_name: HuggingFace model name for Qwen3 reranker
            top_n: Number of top documents to return after reranking
            instruction: Instruction text for the reranker (default: standard instruction)
            max_length: Maximum sequence length
            use_flash_attention: Whether to use flash attention (requires compatible GPU)
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "transformers and torch libraries are required for Qwen3Reranker. "
                "Install with: pip install transformers>=4.51.0 torch>=2.0.0"
            )

        # Initialize parent class first if it's a Pydantic model
        try:
            super().__init__()
        except TypeError:
            # If parent doesn't require initialization, continue
            pass

        # Store instance variables using object.__setattr__ to bypass Pydantic validation
        # if BaseDocumentCompressor is a Pydantic model
        object.__setattr__(self, '_model_name', model_name)
        object.__setattr__(self, '_top_n', top_n)
        object.__setattr__(self, '_instruction', instruction or 'Given a web search query, retrieve relevant passages that answer the query')
        object.__setattr__(self, '_max_length', max_length)
        object.__setattr__(self, '_use_flash_attention', use_flash_attention)

        # Initialize tokenizer and model
        logger.info(f"Loading Qwen3 Reranker model: {model_name}")
        object.__setattr__(self, 'tokenizer', AutoTokenizer.from_pretrained(model_name, padding_side='left'))

        if use_flash_attention:
            try:
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16,
                    attn_implementation="flash_attention_2"
                ).cuda().eval()
            except Exception as e:
                logger.warning(f"Failed to use flash_attention_2: {e}. Using default.")
                model = AutoModelForCausalLM.from_pretrained(model_name).eval()
        else:
            model = AutoModelForCausalLM.from_pretrained(model_name).eval()

        object.__setattr__(self, 'model', model)

        # Get token IDs for "yes" and "no"
        object.__setattr__(self, 'token_false_id', self.tokenizer.convert_tokens_to_ids("no"))
        object.__setattr__(self, 'token_true_id', self.tokenizer.convert_tokens_to_ids("yes"))

        # Setup prefix and suffix tokens (matching Qwen3-Reranker format)
        prefix = "<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n"
        suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
        object.__setattr__(self, 'prefix_tokens', self.tokenizer.encode(prefix, add_special_tokens=False))
        object.__setattr__(self, 'suffix_tokens', self.tokenizer.encode(suffix, add_special_tokens=False))

        logger.info("Qwen3 Reranker initialized successfully")

    @property
    def top_n(self) -> int:
        """Get top_n value."""
        return self._top_n

    @property
    def instruction(self) -> str:
        """Get instruction text."""
        return self._instruction

    def format_instruction(self, query: str, doc: str) -> str:
        """Format instruction, query, and document for the reranker."""
        return "<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {doc}".format(
            instruction=self._instruction,
            query=query,
            doc=doc
        )

    def process_inputs(self, pairs: List[str]):
        """Process and tokenize input pairs."""
        inputs = self.tokenizer(
            pairs,
            padding=False,
            truncation='longest_first',
            return_attention_mask=False,
            max_length=self._max_length - len(self.prefix_tokens) - len(self.suffix_tokens)
        )

        # Add prefix and suffix tokens
        for i, ele in enumerate(inputs['input_ids']):
            inputs['input_ids'][i] = self.prefix_tokens + ele + self.suffix_tokens

        # Pad inputs
        inputs = self.tokenizer.pad(inputs, padding=True, return_tensors="pt", max_length=self._max_length)

        # Move to model device
        for key in inputs:
            inputs[key] = inputs[key].to(self.model.device)

        return inputs

    def compute_logits(self, inputs) -> List[float]:
        """Compute relevance scores for input pairs."""
        batch_scores = self.model(**inputs).logits[:, -1, :]
        true_vector = batch_scores[:, self.token_true_id]
        false_vector = batch_scores[:, self.token_false_id]
        batch_scores = torch.stack([false_vector, true_vector], dim=1)
        batch_scores = torch.nn.functional.log_softmax(batch_scores, dim=1)
        scores = batch_scores[:, 1].exp().tolist()
        return scores

    def compress_documents(
        self,
        documents: List[Document],
        query: str,
        callbacks: Optional[List] = None,
        **kwargs
    ) -> List[Document]:
        """
        Rerank documents based on query relevance.

        Args:
            documents: List of documents to rerank
            query: Query string
            callbacks: Optional callbacks (ignored, for LangChain compatibility)
            **kwargs: Additional keyword arguments (ignored)

        Returns:
            List of reranked documents (top_n)
        """
        if not documents:
            return []

        # Format pairs for reranking
        pairs = [
            self.format_instruction(query, doc.page_content)
            for doc in documents
        ]

        # Process inputs
        inputs = self.process_inputs(pairs)

        # Compute scores
        scores = self.compute_logits(inputs)

        # Create (document, score) pairs and sort by score
        doc_scores = list(zip(documents, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)

        # Return top_n documents
        reranked_docs = [doc for doc, score in doc_scores[:self._top_n]]

        logger.debug(f"Reranked {len(documents)} documents, returning top {len(reranked_docs)}")
        return reranked_docs
