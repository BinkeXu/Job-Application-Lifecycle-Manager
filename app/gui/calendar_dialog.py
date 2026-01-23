import customtkinter as ctk
import calendar
from datetime import datetime

class CalendarDialog(ctk.CTkToplevel):
    """
    A custom modal dialog for selecting a date.
    Implements a calendar view using the standard 'calendar' module.
    """
    def __init__(self, parent, callback, initial_date=None):
        super().__init__(parent)
        self.callback = callback
        self.title("Select Date")
        self.geometry("300x300")
        self.resizable(False, False)
        
        if initial_date:
            try:
                self.current_date = datetime.strptime(initial_date, "%Y-%m-%d")
            except:
                self.current_date = datetime.now()
        else:
            self.current_date = datetime.now()
            
        self.year = self.current_date.year
        self.month = self.current_date.month
        
        self.setup_ui()
        self.grab_set() # Modal
        
    def setup_ui(self):
        # Header: Month/Year navigation
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=10)
        
        self.prev_btn = ctk.CTkButton(self.header_frame, text="<", width=30, command=self.prev_month)
        self.prev_btn.pack(side="left")
        
        self.lbl_month = ctk.CTkLabel(self.header_frame, text="", font=("Arial", 14, "bold"))
        self.lbl_month.pack(side="left", expand=True)
        
        self.next_btn = ctk.CTkButton(self.header_frame, text=">", width=30, command=self.next_month)
        self.next_btn.pack(side="right")
        
        # Calendar Grid
        self.cal_frame = ctk.CTkFrame(self)
        self.cal_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Weekday headers
        days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for i, day in enumerate(days):
            lbl = ctk.CTkLabel(self.cal_frame, text=day, width=30)
            lbl.grid(row=0, column=i, padx=2, pady=5)
            
        self.day_buttons = []
        self.render_calendar()
        
    def render_calendar(self):
        # Update header
        month_name = calendar.month_name[self.month]
        self.lbl_month.configure(text=f"{month_name} {self.year}")
        
        # Clear old buttons
        for btn in self.day_buttons:
            btn.destroy()
        self.day_buttons.clear()
        
        # Get days
        cal = calendar.monthcalendar(self.year, self.month)
        
        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day != 0:
                    btn = ctk.CTkButton(self.cal_frame, text=str(day), width=30, height=30, fg_color="transparent", border_width=1,
                                      text_color="black",
                                      command=lambda d=day: self.select_day(d))
                    btn.grid(row=r+1, column=c, padx=2, pady=2)
                    
                    # Highlight today if in current month
                    if (day == self.current_date.day and 
                        self.month == self.current_date.month and 
                        self.year == self.current_date.year):
                        btn.configure(fg_color=("gray75", "gray25"))
                        
                    self.day_buttons.append(btn)
                    
    def prev_month(self):
        self.month -= 1
        if self.month == 0:
            self.month = 12
            self.year -= 1
        self.render_calendar()
        
    def next_month(self):
        self.month += 1
        if self.month == 13:
            self.month = 1
            self.year += 1
        self.render_calendar()
        
    def select_day(self, day):
        selected_date = datetime(self.year, self.month, day).strftime("%Y-%m-%d")
        self.callback(selected_date)
        self.destroy()
