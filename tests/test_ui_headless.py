import pytest
from unittest.mock import MagicMock
import sys

class DummyWidget:
    def __init__(self, *args, **kwargs): pass
    def __getattr__(self, name):
        mock = MagicMock()
        return mock
    def __iter__(self):
        return iter([])

class DummyVar:
    def __init__(self, value=""): self.val = value
    def get(self): return self.val
    def set(self, val): self.val = val
    def __getattr__(self, name):
        return MagicMock()

def mock_ctk_environment():
    ctk = MagicMock()
    ctk.CTkFrame = DummyWidget
    ctk.CTkToplevel = DummyWidget
    ctk.CTk = DummyWidget
    ctk.CTkLabel = DummyWidget
    ctk.CTkButton = DummyWidget
    ctk.CTkEntry = DummyWidget
    ctk.CTkOptionMenu = DummyWidget
    ctk.CTkScrollableFrame = DummyWidget
    ctk.CTkTextbox = DummyWidget
    ctk.CTkComboBox = DummyWidget
    ctk.CTkProgressBar = DummyWidget
    ctk.StringVar = DummyVar
    ctk.IntVar = DummyVar
    
    sys.modules['customtkinter'] = ctk
    sys.modules['tkinter'] = MagicMock()
    sys.modules['tkinter.messagebox'] = MagicMock()
    sys.modules['matplotlib'] = MagicMock()
    sys.modules['matplotlib.pyplot'] = MagicMock()
    sys.modules['matplotlib.backends'] = MagicMock()
    sys.modules['matplotlib.backends.backend_tkagg'] = MagicMock()
    sys.modules['matplotlib.figure'] = MagicMock()
    sys.modules['CTkToolTip'] = MagicMock()
    sys.modules['tkcalendar'] = MagicMock()
    sys.modules['app.utils.tooltip'] = MagicMock()

def test_all_gui_components_headless(mocker):
    mock_ctk_environment()
    
    mocker.patch("app.core.config_mgr.is_config_complete", return_value=False)
    mocker.patch("app.core.database.get_analytics_data", return_value=({}, []))
    mocker.patch("app.core.database.get_daily_status_counts", return_value=[])
    mocker.patch("app.core.database.get_detailed_analytics", return_value={"total_apps": 0, "interviews_secured": 0, "oa_count": 0, "hr_call_count": 0, "interviewed_count": 0, "offers_count": 0, "oa_roles_list": [], "hr_call_roles_list": [], "interview_roles_list": [], "by_status":[], "by_company":[], "by_role":[]})
    mocker.patch("app.core.database.get_applications", return_value=[{"id": 1, "company_name": "Apple", "role_name": "Dev", "folder_path": "", "status": "Applied", "created_at": "2026-01-01"}])
    mocker.patch("app.core.config_mgr.load_config", return_value={"user_name": "", "cv_template_path": "", "cover_letter_template_path": ""})
    
    from app.gui.dashboard import Dashboard
    from app.gui.setup_wizard import SetupWizard
    from app.gui.analytics_view import AnalyticsDashboard
    from app.gui.add_app_dialog import AddAppDialog
    from app.gui.export_dialog import ExportDialog
    from app.gui.interview_manager import InterviewManager
    from app.gui.report_dialog import ReportDialog
    from app.gui.role_mapping_dialog import RoleMappingDialog
    from app.gui.calendar_dialog import CalendarDialog
    
    mock_master = DummyWidget()
    
    dash = Dashboard(mock_master)
    # Test pagination functionality
    assert dash.current_page == 1
    
    # Test status filtering
    mock_apps = []
    for i in range(50):
        status = "OA" if i % 2 == 0 else "Applied"
        mock_apps.append({"id": i, "company_name": "A", "role_name": "D", "folder_path": "", "status": status, "created_at": "2026-01-01"})
    mocker.patch("app.gui.dashboard.get_applications", return_value=mock_apps)
    
    # Refresh list and verify all are retrieved initially
    dash.refresh_list()
    assert len(dash._all_apps) == 50
    
    # Filter by OA status
    dash.status_filter_var.set("OA")
    dash.refresh_list()
    assert len(dash._all_apps) == 25
    assert all(app['status'] == "OA" for app in dash._all_apps)
    
    # Reset filter
    dash.status_filter_var.set("All Statuses")
    dash.refresh_list()
    assert len(dash._all_apps) == 50

    dash.next_page()
    assert dash.current_page == 2
    dash.next_page()
    assert dash.current_page == 3
    dash.next_page() # Clamp at max page
    assert dash.current_page == 3
    dash.prev_page()
    assert dash.current_page == 2
    dash.prev_page()
    assert dash.current_page == 1
    dash.prev_page() # Clamp at min page
    assert dash.current_page == 1
    
    # Test direct page selection entry submission
    dash.page_entry.get = MagicMock(return_value="2")
    dash.on_page_entry_submit()
    assert dash.current_page == 2
    dash.page_entry.get = MagicMock(return_value="3")
    dash.on_page_entry_submit()
    assert dash.current_page == 3
    dash.page_entry.get = MagicMock(return_value="1")
    dash.on_page_entry_submit()
    assert dash.current_page == 1
    
    dash.search_query = DummyVar("test")
    dash.filter_applications()
    dash.scan_folders()
    
    sw = SetupWizard(mock_master, lambda: None)
    sw.finish_setup()
    
    av = AnalyticsDashboard(mock_master)
    av.set_last_7_days()
    av.clear_dates()
    av.set_last_14_days()
    av.set_last_30_days()
    av.open_summary_report()
    
    add = AddAppDialog(mock_master, lambda: None)
    add.save_app()
    
    exp = ExportDialog(mock_master, [{"id": 1, "company_name": "A"}])
    exp.start_export()
    
    im = InterviewManager(mock_master, 1, "Google", "Dev")
    im.save_note()
    
    dummy_metrics = {
        "total_apps": 0,
        "oa_count": 0,
        "hr_call_count": 0,
        "interviews_secured": 0,
        "offers_count": 0,
        "interview_roles_list": [],
        "oa_roles_list": [],
        "hr_call_roles_list": [],
        "by_status": [],
        "by_company": [],
        "by_role": []
    }
    rd = ReportDialog(mock_master, dummy_metrics, "All Time")
    
    rm = RoleMappingDialog(mock_master)
    rm.save_mapping()
    
    cal = CalendarDialog(mock_master, lambda x: None)
    
    assert True 
