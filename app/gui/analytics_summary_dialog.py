import customtkinter as ctk
import threading
from datetime import datetime, timedelta
from tkinter import messagebox
from ..core.database import get_analytics_data, get_interviews_secured_count, get_detailed_analytics
from .report_dialog import ReportDialog
from .calendar_dialog import CalendarDialog

class AnalyticsSummaryDialog(ctk.CTkToplevel):
    """
    A fast, resizable summary modal displayed when clicking 'Analytics'.
    Presents conversion metrics (Interview Rate, Offer Rate), a time-range selector,
    and an unclipped 2-row pipeline funnel breakdown without layout overflow.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Application Analytics Summary")
        self.geometry("860x630")
        self.minsize(760, 560)
        self.resizable(True, True)
        
        # State tracking for date filtering
        self.start_date = None
        self.end_date = None
        self.range_text = "All Time"

        # Center dialog relative to parent
        self.update_idletasks()
        try:
            x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 430
            y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 315
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        self.setup_ui()
        self.refresh_summary()
        
    def setup_ui(self):
        """Builds the summary view with two-row header, KPI cards, 2-row funnel grid, and actions."""
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=25, pady=(15, 10))

        # 1. Header Frame: Title & Subtitle (Row 1)
        header_row1 = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_row1.pack(fill="x", pady=(0, 4))
        
        ctk.CTkLabel(
            header_row1, 
            text="📈 Application Analytics Summary", 
            font=("Arial", 20, "bold")
        ).pack(side="left", anchor="w")
        
        self.lbl_active_range = ctk.CTkLabel(
            header_row1, 
            text="Timeframe: All Time", 
            text_color="#3B8ED0", 
            font=("Arial", 12, "bold")
        )
        self.lbl_active_range.pack(side="right", anchor="e")

        # 2. Timeframe Controls Bar (Row 2 - Dedicated row prevents any horizontal crowding)
        time_bar = ctk.CTkFrame(self.main_container, fg_color="transparent")
        time_bar.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            time_bar, 
            text="Filter Timeframe:", 
            font=("Arial", 12, "bold"), 
            text_color="gray"
        ).pack(side="left", padx=(0, 8))

        self.timeframe_seg = ctk.CTkSegmentedButton(
            time_bar,
            values=["All Time", "7 Days", "14 Days", "30 Days", "YTD"],
            command=self.on_preset_selected
        )
        self.timeframe_seg.set("All Time")
        self.timeframe_seg.pack(side="left", padx=(0, 8))

        self.btn_custom_cal = ctk.CTkButton(
            time_bar,
            text="📅 Custom...",
            width=85,
            height=28,
            fg_color="#4B5563",
            hover_color="#374151",
            command=self.open_custom_range_picker
        )
        self.btn_custom_cal.pack(side="left")

        # 3. Key Metrics Overarching Cards (Row 3)
        self.kpi_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.kpi_frame.pack(fill="x", pady=(0, 15))
        
        self.card_total_val, self.card_total_sub = self._create_card(
            self.kpi_frame, "Total Applications", "0", "#3B8ED0", "All tracked submissions"
        )
        self.card_interview_val, self.card_interview_sub = self._create_card(
            self.kpi_frame, "Interview Rate", "0.0%", "#8B5CF6", "0 of 0 reached interview"
        )
        self.card_offer_val, self.card_offer_sub = self._create_card(
            self.kpi_frame, "Offer Rate", "0.0%", "#10B981", "0 of 0 received offer"
        )

        # 4. Pipeline Funnel Breakdown (2-row grid ensures every badge is 100% visible)
        funnel_frame = ctk.CTkFrame(self.main_container)
        funnel_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        ctk.CTkLabel(
            funnel_frame, 
            text="Pipeline Funnel Breakdown", 
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=15, pady=(10, 6))

        # Row 1: Pipeline Stages (Applied -> OA -> HR Call -> Interviewed)
        row1_container = ctk.CTkFrame(funnel_frame, fg_color="transparent")
        row1_container.pack(fill="x", padx=12, pady=(0, 6))

        # Row 2: Final Outcomes (Offer, Rejected, Ghosted)
        row2_container = ctk.CTkFrame(funnel_frame, fg_color="transparent")
        row2_container.pack(fill="x", padx=12, pady=(0, 12))

        self.funnel_row1 = [
            ("Applied", "#3B8ED0"),
            ("OA", "#0891B2"),
            ("HR Call", "#DB2777"),
            ("Interviewed", "#8B5CF6")
        ]
        self.funnel_row2 = [
            ("Offer", "#10B981"),
            ("Rejected", "#EF4444"),
            ("Ghosted", "#F59E0B")
        ]

        self.funnel_count_labels = {}
        for title, color in self.funnel_row1:
            self._create_funnel_badge(row1_container, title, color)

        for title, color in self.funnel_row2:
            self._create_funnel_badge(row2_container, title, color)

        # 5. Explanatory Note
        note_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        note_frame.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            note_frame,
            text="Tip: Click 'View Full Report' for detailed role and company tables, or 'View Charts' for visual graphs.",
            font=("Arial", 11, "italic"),
            text_color="gray"
        ).pack(anchor="w")

        # 6. Bottom Action Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=25, pady=(0, 18))
        
        self.btn_full_report = ctk.CTkButton(
            btn_frame, 
            text="📄 View Full Report", 
            width=160, 
            height=34,
            font=("Arial", 13, "bold"),
            fg_color="#10B981", 
            hover_color="#059669", 
            command=self.open_full_report
        )
        self.btn_full_report.pack(side="left", padx=(0, 10))

        self.btn_charts = ctk.CTkButton(
            btn_frame, 
            text="📊 View Charts", 
            width=140, 
            height=34,
            fg_color="#3B8ED0", 
            hover_color="#2563EB", 
            command=self.open_visual_charts
        )
        self.btn_charts.pack(side="left", padx=(0, 10))

        self.btn_close = ctk.CTkButton(
            btn_frame, 
            text="Close", 
            width=100, 
            height=34,
            fg_color="gray", 
            hover_color="#4B4B4B", 
            command=self.destroy
        )
        self.btn_close.pack(side="right")

    def _create_funnel_badge(self, parent, title, color):
        """Creates a funnel counter badge with 64px height preventing any text or digit clipping."""
        badge = ctk.CTkFrame(parent, fg_color=color, corner_radius=8, height=64)
        badge.pack(side="left", fill="both", expand=True, padx=4)
        badge.pack_propagate(False)
        
        ctk.CTkLabel(badge, text=title, text_color="white", font=("Arial", 11, "bold")).pack(pady=(6, 1))
        cnt_lbl = ctk.CTkLabel(badge, text="0", text_color="white", font=("Arial", 18, "bold"))
        cnt_lbl.pack(pady=(0, 6))
        self.funnel_count_labels[title] = cnt_lbl

    def _create_card(self, parent, title, value, color, subtitle=None):
        """Creates a metric card returning references to value and subtitle labels."""
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=10, height=90)
        card.pack(side="left", fill="both", expand=True, padx=5)
        card.pack_propagate(False)
        
        ctk.CTkLabel(card, text=title, text_color="white", font=("Arial", 12)).pack(pady=(8, 2))
        val_lbl = ctk.CTkLabel(card, text=str(value), text_color="white", font=("Arial", 22, "bold"))
        val_lbl.pack(pady=(0, 2))
        sub_lbl = None
        if subtitle:
            sub_lbl = ctk.CTkLabel(card, text=subtitle, text_color="#E0E7FF", font=("Arial", 10))
            sub_lbl.pack(pady=(0, 6))
        return val_lbl, sub_lbl

    def on_preset_selected(self, choice):
        """Handles time range preset selections from the segmented button."""
        now = datetime.now()
        if choice == "7 Days":
            self.start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
            self.end_date = now.strftime("%Y-%m-%d")
            self.range_text = f"{self.start_date} to {self.end_date}"
        elif choice == "14 Days":
            self.start_date = (now - timedelta(days=14)).strftime("%Y-%m-%d")
            self.end_date = now.strftime("%Y-%m-%d")
            self.range_text = f"{self.start_date} to {self.end_date}"
        elif choice == "30 Days":
            self.start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
            self.end_date = now.strftime("%Y-%m-%d")
            self.range_text = f"{self.start_date} to {self.end_date}"
        elif choice == "YTD":
            self.start_date = datetime(now.year, 1, 1).strftime("%Y-%m-%d")
            self.end_date = now.strftime("%Y-%m-%d")
            self.range_text = f"{self.start_date} to {self.end_date}"
        else: # "All Time"
            self.start_date = None
            self.end_date = None
            self.range_text = "All Time"

        self.refresh_summary()

    def open_custom_range_picker(self):
        """Opens a sequential start & end calendar picker for a custom date range."""
        def on_start_chosen(start_str):
            def on_end_chosen(end_str):
                self.start_date = start_str
                self.end_date = end_str
                self.range_text = f"{start_str} to {end_str}"
                try:
                    self.timeframe_seg.set("")
                except Exception:
                    pass
                self.refresh_summary()
            CalendarDialog(self, on_end_chosen, start_str)
        CalendarDialog(self, on_start_chosen)

    def refresh_summary(self):
        """Queries the database with the active date filter and updates all metrics."""
        status_counts, _ = get_analytics_data(self.start_date, self.end_date)
        total = sum(status_counts.values()) if status_counts else 0
        offers = status_counts.get("Offer", 0) if status_counts else 0
        interviewed = get_interviews_secured_count(self.start_date, self.end_date)
        
        interview_rate = (interviewed / total * 100) if total > 0 else 0.0
        offer_rate = (offers / total * 100) if total > 0 else 0.0

        # Update Active Range label
        self.lbl_active_range.configure(text=f"Timeframe: {self.range_text}")

        # Update Top KPI Cards
        self.card_total_val.configure(text=str(total))
        sub_total_text = "All tracked submissions" if not self.start_date else f"{self.range_text}"
        if self.card_total_sub:
            self.card_total_sub.configure(text=sub_total_text)

        self.card_interview_val.configure(text=f"{interview_rate:.1f}%")
        if self.card_interview_sub:
            self.card_interview_sub.configure(text=f"{interviewed} of {total} reached interview")

        self.card_offer_val.configure(text=f"{offer_rate:.1f}%")
        if self.card_offer_sub:
            self.card_offer_sub.configure(text=f"{offers} of {total} received offer")

        # Update Pipeline Funnel Badges
        all_stages = self.funnel_row1 + self.funnel_row2
        for title, _ in all_stages:
            count = status_counts.get(title, 0) if status_counts else 0
            if title in self.funnel_count_labels:
                self.funnel_count_labels[title].configure(text=str(count))

    def open_full_report(self):
        """
        Launches the Full Report in the foreground while releasing the summary modal lock.
        Hides the summary dialog so it never sits behind the report, and smoothly restores
        the summary when the report is closed.
        """
        self.btn_full_report.configure(state="disabled", text="Loading Report...")
        
        def fetch():
            try:
                metrics = get_detailed_analytics(self.start_date, self.end_date, skip_llm=True)
                if self.winfo_exists():
                    self.after(0, self._show_report, metrics)
            except Exception as e:
                print(f"Error fetching detailed report: {e}")
                if self.winfo_exists():
                    self.after(0, lambda: self.btn_full_report.configure(state="normal", text="📄 View Full Report"))

        threading.Thread(target=fetch, daemon=True).start()

    def _show_report(self, metrics):
        self.btn_full_report.configure(state="normal", text="📄 View Full Report")
        
        # 1. Release modal lock and hide summary so it never sits behind the report
        self.grab_release()
        self.withdraw()
        
        # 2. Launch ReportDialog as a top-level window
        report = ReportDialog(self.master, metrics, self.range_text)
        report.lift()
        report.focus_force()
        
        # 3. Clean callback to restore summary when ReportDialog is closed
        def on_report_close():
            try:
                report.destroy()
            except Exception:
                pass
            if self.winfo_exists():
                self.deiconify()
                self.lift()
                self.grab_set()
                
        report.protocol("WM_DELETE_WINDOW", on_report_close)
        report.close_btn.configure(command=on_report_close)

    def open_visual_charts(self):
        """
        Launches the interactive charts dashboard in the foreground while releasing the summary modal lock.
        Hides the summary dialog and smoothly restores it when the charts window is closed.
        """
        self.grab_release()
        self.withdraw()
        
        from .analytics_view import AnalyticsDashboard
        dash = AnalyticsDashboard(self.master, start_date=self.start_date, end_date=self.end_date)
        dash.lift()
        dash.focus_force()
        
        def on_dash_close():
            try:
                dash.destroy()
            except Exception:
                pass
            if self.winfo_exists():
                self.deiconify()
                self.lift()
                self.grab_set()
                
        dash.protocol("WM_DELETE_WINDOW", on_dash_close)
