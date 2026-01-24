import customtkinter as ctk
import tkinter as tk
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox
from ..core.database import get_analytics_data, get_daily_status_counts
from .calendar_dialog import CalendarDialog

class AnalyticsDashboard(ctk.CTkToplevel):
    """
    A Toplevel window that displays analytics for the job applications.
    Features:
    - Date filtering with custom calendar picker
    - Status distribution chart (Pie)
    - Application timeline chart (Stacked Bar)
    - Manual tooltips for chart interactivity
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Application Analytics")
        self.geometry("1000x800")
        
        # Set window icon if available (optional)
        # self.iconbitmap("icon.ico")

        self.setup_ui()
        self.refresh_charts()

    def setup_ui(self):
        """Initializes the UI components: Toolbar, Charts, and Footer."""
        # 1. Toolbar for Filters
        self.toolbar = ctk.CTkFrame(self)
        self.toolbar.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(self.toolbar, text="From:").pack(side="left", padx=5)
        self.start_date_var = ctk.StringVar()
        self.start_entry = ctk.CTkEntry(self.toolbar, placeholder_text="YYYY-MM-DD", width=100, textvariable=self.start_date_var)
        self.start_entry.pack(side="left", padx=5)
        
        self.btn_cal_start = ctk.CTkButton(self.toolbar, text="📅", width=30, command=lambda: self.open_cal(self.start_date_var))
        self.btn_cal_start.pack(side="left", padx=(0, 5))
        
        ctk.CTkLabel(self.toolbar, text="To:").pack(side="left", padx=5)
        self.end_date_var = ctk.StringVar()
        self.end_entry = ctk.CTkEntry(self.toolbar, placeholder_text="YYYY-MM-DD", width=100, textvariable=self.end_date_var)
        self.end_entry.pack(side="left", padx=5)
        
        self.btn_cal_end = ctk.CTkButton(self.toolbar, text="📅", width=30, command=lambda: self.open_cal(self.end_date_var))
        self.btn_cal_end.pack(side="left", padx=(0, 5))
        
        self.apply_btn = ctk.CTkButton(self.toolbar, text="Apply Filter", width=100, command=self.refresh_charts)
        self.apply_btn.pack(side="left", padx=10)
        
        self.last_7_btn = ctk.CTkButton(self.toolbar, text="Last 7 Days", width=80, fg_color="gray", command=self.set_last_7_days)
        self.last_7_btn.pack(side="left", padx=5)
        
        self.last_14_btn = ctk.CTkButton(self.toolbar, text="Last 14 Days", width=80, fg_color="gray", command=self.set_last_14_days)
        self.last_14_btn.pack(side="left", padx=5)
        
        self.last_30_btn = ctk.CTkButton(self.toolbar, text="Last 30 Days", width=90, fg_color="gray", command=self.set_last_30_days)
        self.last_30_btn.pack(side="left", padx=5)
        
        self.clear_btn = ctk.CTkButton(self.toolbar, text="All Time", width=80, fg_color="gray", command=self.clear_dates)
        self.clear_btn.pack(side="left", padx=5)

        # View Report Button (Primary Action Style)
        self.report_btn = ctk.CTkButton(self.toolbar, text="📄 View Report", width=100, command=self.open_summary_report)
        self.report_btn.pack(side="right", padx=10)

        # 2. Charts Area
        self.charts_frame = ctk.CTkFrame(self)
        self.charts_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # We'll use a 2x1 grid (or 1x2) for charts
        self.charts_frame.grid_columnconfigure(0, weight=1)
        self.charts_frame.grid_columnconfigure(1, weight=1)
        self.charts_frame.grid_rowconfigure(0, weight=1)

        # Matplotlib Figure
        self.fig = plt.figure(figsize=(10, 5), dpi=100)
        self.ax1 = self.fig.add_subplot(121) # Pie Chart
        self.ax2 = self.fig.add_subplot(122) # Line/Bar Chart
        
        # Adjust layout
        self.fig.tight_layout(pad=3.0)
        
        # Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.charts_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Connect Hover Event
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_hover)
        
        # Tooltip Annotation (Hidden initially)
        self.annot = self.ax1.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
                                     bbox=dict(boxstyle="round", fc="w"),
                                     arrowprops=dict(arrowstyle="->"))
        self.annot.set_visible(False)
        
        self.annot2 = self.ax2.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
                                      bbox=dict(boxstyle="round", fc="w"),
                                      arrowprops=dict(arrowstyle="->"))
        self.annot2.set_visible(False)

        # 3. Summary Footer
        self.footer_label = ctk.CTkLabel(self, text="", font=("Arial", 12))
        self.footer_label.pack(side="bottom", pady=10)

    def open_cal(self, variable):
        CalendarDialog(self, lambda date: variable.set(date), variable.get())

    def set_last_7_days(self):
        end = datetime.now()
        start = end - timedelta(days=7)
        self.start_date_var.set(start.strftime("%Y-%m-%d"))
        self.end_date_var.set(end.strftime("%Y-%m-%d"))
        self.refresh_charts()

    def set_last_14_days(self):
        """Quick-filter shortcut to set the date range to the previous 14 days."""
        end = datetime.now()
        start = end - timedelta(days=14)
        self.start_date_var.set(start.strftime("%Y-%m-%d"))
        self.end_date_var.set(end.strftime("%Y-%m-%d"))
        self.refresh_charts()

    def set_last_30_days(self):
        """Quick-filter shortcut to set the date range to the previous 30 days."""
        end = datetime.now()
        start = end - timedelta(days=30)
        self.start_date_var.set(start.strftime("%Y-%m-%d"))
        self.end_date_var.set(end.strftime("%Y-%m-%d"))
        self.refresh_charts()

    def clear_dates(self):
        self.start_date_var.set("")
        self.end_date_var.set("")
        self.refresh_charts()

    def refresh_charts(self):
        start = self.start_date_var.get().strip()
        end = self.end_date_var.get().strip()
        
        # Simple Validation
        if start and not self.validate_date(start):
            messagebox.showerror("Error", "Invalid Start Date. Use YYYY-MM-DD")
            return
        if end and not self.validate_date(end):
            messagebox.showerror("Error", "Invalid End Date. Use YYYY-MM-DD")
            return

        # Fetch Data
        status_counts, _ = get_analytics_data(start if start else None, end if end else None)
        daily_breakdown = get_daily_status_counts(start if start else None, end if end else None)
        
        # Clear Axes
        self.ax1.clear()
        self.ax2.clear()
        
        # Color Map
        color_map = {
            "Applied": "#3B8ED0",
            "Interviewing": "#8B5CF6", # Purple
            "Rejected": "#EF4444", # Red
            "Offer": "#10B981", # Green
            "Ghosted": "#F59E0B" # Orange
        }
        
        # 1. Status Distribution (Pie Chart)
        if status_counts:
            # Custom Colors
            colors = []
            labels = list(status_counts.keys())
            values = list(status_counts.values())
            
            colors = [color_map.get(l, "#6B7280") for l in labels]
            
            wedges, texts, autotexts = self.ax1.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
            
            # Attach data for tooltips
            for i, wedge in enumerate(wedges):
                wedge.my_label = labels[i]
                wedge.my_value = values[i]

            self.ax1.set_title("Application Status")
        else:
            self.ax1.text(0.5, 0.5, "No Data", ha='center')

        # 2. Timeline (Stacked Bar Chart)
        if daily_breakdown:
            # Process data into {date: {status: count}}
            data_map = {}
            all_statuses = set()
            for day, status, count in daily_breakdown:
                if day not in data_map:
                    data_map[day] = {}
                data_map[day][status] = count
                all_statuses.add(status)
            
            dates_sorted = sorted(data_map.keys())
            x_dates = [datetime.strptime(d, "%Y-%m-%d") for d in dates_sorted]
            
            bottoms = [0] * len(x_dates)
            
            for status in sorted(list(all_statuses)):
                counts = [data_map[d].get(status, 0) for d in dates_sorted]
                color = color_map.get(status, "#6B7280")
                bars = self.ax2.bar(x_dates, counts, bottom=bottoms, label=status, color=color, width=0.8)
                # Store status label in bar object for tooltip
                for bar in bars:
                     bar.set_picker(True) # Enable picking if needed, but we use contains
                     bar._label_status = status 

                # Update bottoms for next stack
                bottoms = [b + c for b, c in zip(bottoms, counts)]
            
            self.ax2.set_title("Applications Added")
            self.ax2.tick_params(axis='x', rotation=45)
            self.ax2.legend(loc='upper right', fontsize='small')
        else:
            self.ax2.text(0.5, 0.5, "No Data", ha='center')

        # Update Footer
        total = sum(status_counts.values()) if status_counts else 0
        summary_text = f"Total: {total}"
        if status_counts:
            for s, c in status_counts.items():
                summary_text += f" | {s}: {c}"
        self.footer_label.configure(text=summary_text)

        self.canvas.draw()
        
    def update_tooltip(self, annot, text, event):
        annot.xy = (event.xdata, event.ydata)
        annot.set_text(text)
        annot.get_bbox_patch().set_alpha(0.9)
        annot.set_visible(True)
        self.fig.canvas.draw_idle()

    def on_hover(self, event):
        """
        Callback for mouse motion over the canvas.
        Delegates to handle_hover for actual tooltip logic.
        """
        self.handle_hover(event)

    def handle_hover(self, event):
        """
        Updated logic to handle hovering over charts.
        Detects if mouse is over a Pie Wedge or Bar Rect and displays the appropriate tooltip.
        """
        # 1. Clear existing tooltips if not hovering (default state)
        if self.annot.get_visible():
            self.annot.set_visible(False)
            self.fig.canvas.draw_idle()
        if self.annot2.get_visible():
            self.annot2.set_visible(False)
            self.fig.canvas.draw_idle()

        # 2. Check if hovering over Pie Chart (ax1)
        if event.inaxes == self.ax1:
            for wedge in self.ax1.patches:
                cont, _ = wedge.contains(event)
                if cont:
                    # We stored 'my_label' and 'my_value' on the artist objects during refresh_charts
                    label = getattr(wedge, 'my_label', '')
                    val = getattr(wedge, 'my_value', '')
                    if label:
                         self.update_tooltip(self.annot, f"{label}: {val}", event)
                    break
        
        # 3. Check if hovering over Bar Chart (ax2)
        elif event.inaxes == self.ax2:
            for bar in self.ax2.patches:
                cont, _ = bar.contains(event)
                if cont:
                    # We stored '_label_status' on the bar objects during refresh_charts
                    status = getattr(bar, '_label_status', 'Unknown')
                    height = bar.get_height()
                    if height > 0: # Only show tooltip for visible bars
                        self.update_tooltip(self.annot2, f"{status}: {int(height)}", event)
                    break


    def open_summary_report(self):
        """
        Gathers detailed analytics data for the current date range and 
        displays it in a structured ReportDialog modal.
        """
        start = self.start_date_var.get().strip()
        end = self.end_date_var.get().strip()
        
        # Query the database for granular metrics based on selected dates.
        from ..core.database import get_detailed_analytics
        metrics = get_detailed_analytics(start if start else None, end if end else None)
        
        # Prepare a readable date range string for the report title.
        range_text = f"{start} to {end}" if(start and end) else "All Time"
        
        # Open the specialized reporting component.
        from .report_dialog import ReportDialog
        ReportDialog(self, metrics, range_text)

    def validate_date(self, date_text):
        try:
            datetime.strptime(date_text, '%Y-%m-%d')
            return True
        except ValueError:
            return False
