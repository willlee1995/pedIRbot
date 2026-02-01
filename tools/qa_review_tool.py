"""
Q&A Review Tool for IR Experts
A simple GUI to review KB Q&A files, add comments, and save evaluations to CSV
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import re
import csv
from datetime import datetime
from pathlib import Path
import markdown
from tkhtmlview import HTMLText

class ScrolledHTMLText(ttk.Frame):
    """A scrollable HTML text widget"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.html_widget = HTMLText(self, **kwargs)
        self.vbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.html_widget.yview)
        self.html_widget.configure(yscrollcommand=self.vbar.set)

        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.html_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def set_html(self, html_content):
        self.html_widget.set_html(html_content)

    def set_markdown(self, md_content):
        """Convert markdown to HTML and display"""
        # Simple markdown to HTML conversion without custom CSS to avoid rendering artifacts
        # Using extensions to support tables and code blocks
        html = markdown.markdown(md_content, extensions=['fenced_code', 'tables', 'nl2br'])
        self.set_html(html)

class QAReviewTool:
    def __init__(self, root):
        self.root = root
        self.root.title("PediIR-Bot Q&A Review Tool")
        self.root.geometry("1200x800")

        # Data storage
        self.qa_files = []
        self.current_file_index = 0
        self.qa_pairs = []
        self.current_qa_index = 0
        self.evaluations = {}  # {file_path: {qa_index: {rating, comment, ...}}}

        # KB directory
        self.kb_dir = Path(r"d:\Development area\pedIRbot\KB")

        self.setup_ui()
        self.load_qa_files()

    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Left panel - File list
        left_frame = ttk.LabelFrame(main_frame, text="Q&A Files", padding="5")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.file_listbox = tk.Listbox(left_frame, width=40, height=25)
        self.file_listbox.pack(fill=tk.BOTH, expand=True)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)

        # Progress label
        self.progress_label = ttk.Label(left_frame, text="Progress: 0/0")
        self.progress_label.pack(pady=5)

        # Middle panel - Q&A content
        middle_frame = ttk.LabelFrame(main_frame, text="Q&A Content", padding="5")
        middle_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        main_frame.columnconfigure(1, weight=2)

        # Q&A navigation
        nav_frame = ttk.Frame(middle_frame)
        nav_frame.pack(fill=tk.X, pady=(0, 5))

        self.prev_qa_btn = ttk.Button(nav_frame, text="← Previous Q&A", command=self.prev_qa)
        self.prev_qa_btn.pack(side=tk.LEFT)

        self.qa_label = ttk.Label(nav_frame, text="Q&A 0/0", font=('Arial', 12, 'bold'))
        self.qa_label.pack(side=tk.LEFT, padx=20)

        self.next_qa_btn = ttk.Button(nav_frame, text="Next Q&A →", command=self.next_qa)
        self.next_qa_btn.pack(side=tk.LEFT)

        # Question display
        ttk.Label(middle_frame, text="Question 問題:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.question_view = ScrolledHTMLText(middle_frame)
        self.question_view.pack(fill=tk.X, pady=(0, 10), expand=False, ipady=40) # Fixed small height

        # Answer display
        ttk.Label(middle_frame, text="Answer 答案:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.answer_view = ScrolledHTMLText(middle_frame)
        self.answer_view.pack(fill=tk.BOTH, expand=True, pady=(0, 10)) # Expands to fill rest

        # Right panel - Evaluation
        right_frame = ttk.LabelFrame(main_frame, text="Evaluation", padding="5")
        right_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        main_frame.columnconfigure(2, weight=1)

        # Rating - 5-Point Likert Scale for Accuracy Evaluation
        ttk.Label(right_frame, text="Rating 評分 (1-5):", font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        self.rating_var = tk.IntVar(value=0)
        ratings = [
            ("5 - Completely correct, no important info to add\n     完全正確，無需補充重要資訊", 5),
            ("4 - Very good, only very few inaccuracies\n     非常好，只有很少不準確處", 4),
            ("3 - Overall acceptable, partially incorrect/missing\n     整體可接受，部分不正確或遺漏", 3),
            ("2 - Mostly incorrect/Most important info missing\n     大部分不正確／大部分重要資訊遺漏", 2),
            ("1 - Major errors, potentially harmful\n     重大錯誤，可能有害", 1),
        ]

        for text, value in ratings:
            rb = ttk.Radiobutton(right_frame, text=text, value=value, variable=self.rating_var)
            rb.pack(anchor=tk.W, pady=2)

        ttk.Separator(right_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # Specific issues checkboxes
        ttk.Label(right_frame, text="Issues 問題:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        self.issue_vars = {}
        issues = [
            ("Factually incorrect 事實錯誤", "factual_error"),
            ("Outdated info 資訊過時", "outdated"),
            ("Missing info 資訊不完整", "missing_info"),
            ("Wrong HKCH details HKCH資料錯誤", "hkch_error"),
            ("Translation issue 翻譯問題", "translation")
        ]

        for text, key in issues:
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(right_frame, text=text, variable=var)
            cb.pack(anchor=tk.W, pady=1)
            self.issue_vars[key] = var

        ttk.Separator(right_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # Comments
        ttk.Label(right_frame, text="Comments 意見:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.comment_text = scrolledtext.ScrolledText(right_frame, height=8, wrap=tk.WORD)
        self.comment_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Suggested correction
        ttk.Label(right_frame, text="Suggested Correction 建議修正:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.correction_text = scrolledtext.ScrolledText(right_frame, height=6, wrap=tk.WORD)
        self.correction_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Save button
        self.save_btn = ttk.Button(right_frame, text="💾 Save Evaluation", command=self.save_current_evaluation)
        self.save_btn.pack(fill=tk.X, pady=5)

        # Bottom buttons
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(10, 0))

        ttk.Button(bottom_frame, text="📁 Export All to CSV", command=self.export_to_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="📂 Load Previous Session", command=self.load_from_csv).pack(side=tk.LEFT, padx=5)

        # Reviewer name
        ttk.Label(bottom_frame, text="Reviewer 審核人:").pack(side=tk.RIGHT)
        self.reviewer_entry = ttk.Entry(bottom_frame, width=20)
        self.reviewer_entry.pack(side=tk.RIGHT, padx=5)
        self.reviewer_entry.insert(0, "IR Expert")

        main_frame.rowconfigure(0, weight=1)

    def load_qa_files(self):
        """Find all Q&A markdown files in KB directory"""
        self.qa_files = []
        for qa_file in self.kb_dir.rglob("*_qa.md"):
            self.qa_files.append(qa_file)

        self.qa_files.sort()

        self.file_listbox.delete(0, tk.END)
        for f in self.qa_files:
            rel_path = f.relative_to(self.kb_dir)
            self.file_listbox.insert(tk.END, str(rel_path))

        self.update_progress()

        if self.qa_files:
            self.file_listbox.selection_set(0)
            self.load_current_file()

    def parse_qa_file(self, file_path):
        """Parse a Q&A markdown file into question-answer pairs"""
        qa_pairs = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by Q&A headers (## Q1:, ## Q2:, etc.)
        pattern = r'## Q(\d+):'
        parts = re.split(pattern, content)

        # parts[0] is header, then alternating: qa_num, content
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                qa_num = parts[i]
                qa_content = parts[i + 1]

                # Split into question and answer
                lines = qa_content.strip().split('\n')

                # First few lines are the question (including Chinese)
                question_lines = []
                answer_lines = []
                in_answer = False

                for line in lines:
                    if line.strip().startswith('**Answer') or line.strip().startswith('答案'):
                        in_answer = True

                    if in_answer:
                        answer_lines.append(line)
                    else:
                        question_lines.append(line)

                question = '\n'.join(question_lines).strip()
                answer = '\n'.join(answer_lines).strip()

                qa_pairs.append({
                    'number': qa_num,
                    'question': question,
                    'answer': answer,
                    'raw': f"## Q{qa_num}:{qa_content}"
                })

        return qa_pairs

    def on_file_select(self, event):
        selection = self.file_listbox.curselection()
        if selection:
            self.current_file_index = selection[0]
            self.current_qa_index = 0
            self.load_current_file()

    def load_current_file(self):
        if not self.qa_files:
            return

        file_path = self.qa_files[self.current_file_index]
        self.qa_pairs = self.parse_qa_file(file_path)
        self.display_current_qa()

    def display_current_qa(self):
        if not self.qa_pairs:
            return

        qa = self.qa_pairs[self.current_qa_index]

        # Update Q&A label
        self.qa_label.config(text=f"Q&A {self.current_qa_index + 1}/{len(self.qa_pairs)}")

        # Display question
        self.question_view.set_markdown(qa['question'])

        # Display answer
        self.answer_view.set_markdown(qa['answer'])

        # Load existing evaluation if any
        self.load_evaluation()

        # Update navigation buttons
        self.prev_qa_btn.config(state=tk.NORMAL if self.current_qa_index > 0 else tk.DISABLED)
        self.next_qa_btn.config(state=tk.NORMAL if self.current_qa_index < len(self.qa_pairs) - 1 else tk.DISABLED)

    def prev_qa(self):
        self.save_current_evaluation()
        if self.current_qa_index > 0:
            self.current_qa_index -= 1
            self.display_current_qa()

    def next_qa(self):
        self.save_current_evaluation()
        if self.current_qa_index < len(self.qa_pairs) - 1:
            self.current_qa_index += 1
            self.display_current_qa()

    def get_current_key(self):
        """Get unique key for current Q&A"""
        if not self.qa_files or not self.qa_pairs:
            return None
        file_path = str(self.qa_files[self.current_file_index])
        return f"{file_path}::Q{self.qa_pairs[self.current_qa_index]['number']}"

    def save_current_evaluation(self):
        """Save current evaluation to memory"""
        key = self.get_current_key()
        if not key:
            return

        issues = [k for k, v in self.issue_vars.items() if v.get()]

        self.evaluations[key] = {
            'file': str(self.qa_files[self.current_file_index].relative_to(self.kb_dir)),
            'qa_number': self.qa_pairs[self.current_qa_index]['number'],
            'question_preview': self.qa_pairs[self.current_qa_index]['question'][:100],
            'rating': self.rating_var.get(),
            'issues': ','.join(issues),
            'comment': self.comment_text.get(1.0, tk.END).strip(),
            'correction': self.correction_text.get(1.0, tk.END).strip(),
            'reviewer': self.reviewer_entry.get(),
            'timestamp': datetime.now().isoformat()
        }

        self.update_progress()

    def load_evaluation(self):
        """Load evaluation for current Q&A if exists"""
        key = self.get_current_key()

        # Reset fields
        self.rating_var.set(0)
        for var in self.issue_vars.values():
            var.set(False)
        self.comment_text.delete(1.0, tk.END)
        self.correction_text.delete(1.0, tk.END)

        if key and key in self.evaluations:
            eval_data = self.evaluations[key]
            self.rating_var.set(int(eval_data.get('rating', 0)))

            issues = eval_data.get('issues', '').split(',')
            for issue in issues:
                if issue in self.issue_vars:
                    self.issue_vars[issue].set(True)

            self.comment_text.insert(tk.END, eval_data.get('comment', ''))
            self.correction_text.insert(tk.END, eval_data.get('correction', ''))

    def update_progress(self):
        """Update progress label"""
        total_qa = sum(len(self.parse_qa_file(f)) for f in self.qa_files)
        reviewed = len([e for e in self.evaluations.values() if e.get('rating') and int(e.get('rating', 0)) > 0])
        self.progress_label.config(text=f"Reviewed: {reviewed}/{total_qa}")

    def export_to_csv(self):
        """Export all evaluations to CSV"""
        if not self.evaluations:
            messagebox.showwarning("No Data", "No evaluations to export")
            return

        # Save current first
        self.save_current_evaluation()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"qa_review_{timestamp}.csv"

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=default_name,
            initialdir=str(self.kb_dir.parent)
        )

        if not file_path:
            return

        fieldnames = ['file', 'qa_number', 'question_preview', 'rating', 'issues',
                      'comment', 'correction', 'reviewer', 'timestamp']

        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for eval_data in self.evaluations.values():
                writer.writerow(eval_data)

        messagebox.showinfo("Export Complete", f"Saved {len(self.evaluations)} evaluations to:\n{file_path}")

    def load_from_csv(self):
        """Load previous session from CSV"""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")],
            initialdir=str(self.kb_dir.parent)
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = f"{self.kb_dir / row['file']}::Q{row['qa_number']}"
                    self.evaluations[key] = row

            self.update_progress()
            self.load_evaluation()
            messagebox.showinfo("Load Complete", f"Loaded {len(self.evaluations)} evaluations")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV: {e}")


def main():
    root = tk.Tk()
    app = QAReviewTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
