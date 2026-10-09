# -*- coding: utf-8 -*-
"""
محلل مساحة القرص — Disk Space Analyzer
Classic Black Ribbon UI + Custom line-art icons (no emojis) + Bilingual (AR/EN)
Developer: Craftou سهيل (عمري 13 حاليا)
"""

import os
import sys
import time
import sqlite3
import ctypes
import hashlib
import csv
import json

try:
    from ctypes import wintypes
    _HAS_WINTYPES = True
except ImportError:
    _HAS_WINTYPES = False

try:
    from send2trash import send2trash as _send2trash
    _HAS_SEND2TRASH = True
except ImportError:
    _HAS_SEND2TRASH = False

from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QRect, QRectF, QPointF, QUrl,
    QStandardPaths, QSize
)
from PyQt6.QtGui import (
    QColor, QBrush, QFont, QDesktopServices, QPainter, QPen,
    QPalette, QIcon, QPixmap, QPainterPath
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTreeWidget, QTreeWidgetItem,
    QSplitter, QProgressBar, QFileDialog, QMessageBox, QHeaderView,
    QSpinBox, QAbstractItemView, QMenu, QStatusBar, QTabWidget,
    QStyle, QStyleOptionViewItem, QStyledItemDelegate, QCheckBox,
    QComboBox, QFrame, QStackedWidget, QTabBar, QSizePolicy,
    QToolButton
)


# ============================================================
#  ثوابت
# ============================================================
SKIP_DIR_NAMES = {"$RECYCLE.BIN", "$Recycle.Bin",
                  "System Volume Information", "Config.Msi"}
USER_SCAN_KEY = "__USER_FILES__"
LTR_EMBED = "\u202A"
POP_DIR = "\u202C"


def ltr(s) -> str:
    if s is None:
        return ""
    return f"{LTR_EMBED}{s}{POP_DIR}"


CATEGORIES = {
    "all": None,
    "video": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
              ".m4v", ".mpg", ".mpeg", ".3gp", ".ts", ".vob", ".rmvb", ".ogv"},
    "image": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif",
              ".webp", ".svg", ".ico", ".heic", ".raw", ".psd", ".ai"},
    "audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a",
              ".opus", ".aiff", ".ape", ".alac", ".mid", ".midi"},
    "document": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
                 ".txt", ".rtf", ".odt", ".ods", ".odp", ".csv", ".md",
                 ".epub", ".mobi", ".djvu"},
    "archive": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
                ".iso", ".cab", ".tgz", ".tbz", ".lz", ".lzma", ".zst"},
    "code": {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp",
             ".cc", ".h", ".hpp", ".cs", ".go", ".rs", ".rb", ".php",
             ".html", ".htm", ".css", ".scss", ".json", ".xml", ".yml",
             ".yaml", ".sh", ".bat", ".ps1", ".sql", ".swift", ".kt"},
    "executable": {".exe", ".msi", ".dll", ".so", ".dylib", ".bin",
                   ".app", ".deb", ".rpm", ".apk", ".appx", ".msix"},
}

JUNK_EXTS = {".tmp", ".temp", ".log", ".cache", ".bak", ".old",
             ".dmp", ".chk", ".part", ".crdownload", ".partial"}


# ============================================================
#  الترجمات
# ============================================================
TR = {
    "en": {
        "app_title": "Disk Space Analyzer",
        "ribbon_home": "Home", "ribbon_tools": "Tools", "ribbon_view": "View",
        "grp_scan": "Scan", "grp_quick": "Quick Scan",
        "grp_filters": "Filters", "grp_actions": "Actions",
        "grp_analysis": "Analysis", "grp_filter_results": "Filter Results",
        "grp_export": "Export", "grp_language": "Language",
        "grp_options": "Options", "grp_info": "About",
        "browse": "Browse", "scan": "Scan", "stop": "Stop", "refresh": "Refresh",
        "user_scan": "User Files", "full_scan": "Full Drive",
        "open": "Open", "reveal": "Reveal",
        "dup": "Duplicates", "empty": "Empty Folders",
        "old": "Old Files", "junk": "Junk Files",
        "export_csv": "CSV", "export_json": "JSON", "export_html": "HTML",
        "toggle_lang": "العربية", "about": "About",
        "path_label": "Path:", "path_placeholder": "Type a path or choose a folder / drive...",
        "category": "Type:", "min_size": "Min MB:", "max_size": "Max MB:",
        "top_results": "Top:", "skip_system": "Skip system folders",
        "cat_all": "All types", "cat_video": "Videos", "cat_image": "Images",
        "cat_audio": "Audio", "cat_document": "Documents",
        "cat_archive": "Archives", "cat_code": "Code",
        "cat_executable": "Executables",
        "filter_ext": "Extensions:", "filter_min": "Min MB:",
        "filter_max": "Max MB:", "filter_age": "Older (days):",
        "filter_apply": "Apply", "filter_reset": "Reset",
        "age_days": "Older than (days):",
        "tab_files": "Large Files", "tab_types": "File Types",
        "tab_tool_results": "Tool Results",
        "col_folder": "Folder", "col_size": "Size", "col_percent": "Percent",
        "col_count": "Files", "col_name": "Name",
        "col_parent": "Parent Folder", "col_ext": "Extension",
        "col_item": "Item", "col_info": "Info",
        "header_folders": "  Top folders by size",
        "header_files": "  Largest files",
        "header_types": "  Space by file type",
        "header_tool_results": "  Tool results",
        "status_ready": "Ready.",
        "status_scanning": "Scanning: {path}",
        "status_user_scan": "Fast scan of user folders ({n} folder(s))...",
        "status_full_scan": "Full drive scan: {path}",
        "status_progress": "Scanned {count:,} files  |  Size: {size}  |  {path}",
        "status_done": "Done  |  Total: {total}  |  Files: {files:,}  |  Folders: {folders:,}",
        "status_stopped": "Scan stopped",
        "status_cache_loaded": "Loaded cache  |  {time}  |  Total: {total}",
        "status_tool_working": "Working: {name}...",
        "msg_warn": "Warning", "msg_error": "Error",
        "msg_no_path": "Please specify a path.",
        "msg_bad_path": "Path does not exist:\n{path}",
        "msg_no_user_dirs": "No user folders were found.",
        "msg_confirm_delete_title": "Confirm Delete",
        "msg_confirm_delete": "Permanently delete {n} item(s)?\n\n{preview}",
        "msg_delete_done": "Delete result",
        "msg_delete_ok": "Deleted {n} item(s).",
        "msg_delete_fail": "Failed: {n}\n{errors}",
        "msg_scan_error": "Scan failed:\n{msg}",
        "msg_not_exist": "Item no longer exists.",
        "msg_copied": "Copied: {path}",
        "msg_trash_done": "Moved {n} item(s) to Trash.",
        "msg_trash_fail": "Failed to trash: {n}\n{errors}",
        "msg_no_drive": "Could not detect the system drive.",
        "msg_no_results": "Please run a scan first.",
        "msg_exported": "Exported: {path}",
        "trash_unavailable": "Move to Trash is not available.",
        "copy_path": "Copy path", "trash": "Move to Trash",
        "delete": "Delete permanently...",
        "no_ext": "(no extension)", "other": "Other",
        "dup_count": "{n} duplicate group(s)", "empty_count": "{n} empty folder(s)",
        "old_count": "{n} old file(s)", "junk_count": "{n} junk file(s)",
        "filter_count": "{n} file(s) after filter",
        "no_results_found": "No results.",
        "dup_group": "Group {i} — {size} × {n}",
        "about_text": (
            "<h3>Disk Space Analyzer</h3>"
            "<p>A bilingual PyQt6 tool to inspect disk usage, find big files, "
            "detect duplicates, and analyze file types.</p>"
            "<p><b>Features:</b><br>"
            "• Fast scan with os.scandir<br>"
            "• SQLite cache<br>"
            "• Duplicate finder (MD5)<br>"
            "• Empty / old / junk files<br>"
            "• CSV / JSON / HTML export</p>"
            "<p style='color:#8ec7ff;font-size:11pt;'>"
            "<b>Developer:</b> Craftou سهيل</p>"
        ),
    },
    "ar": {
        "app_title": "محلل مساحة القرص",
        "ribbon_home": "الرئيسية", "ribbon_tools": "الأدوات", "ribbon_view": "العرض",
        "grp_scan": "الفحص", "grp_quick": "فحص سريع",
        "grp_filters": "الفلاتر", "grp_actions": "إجراءات",
        "grp_analysis": "تحليل", "grp_filter_results": "تصفية النتائج",
        "grp_export": "تصدير", "grp_language": "اللغة",
        "grp_options": "خيارات", "grp_info": "حول",
        "browse": "استعراض", "scan": "فحص", "stop": "إيقاف", "refresh": "تحديث",
        "user_scan": "ملفات المستخدم", "full_scan": "القرص كامل",
        "open": "فتح", "reveal": "إظهار",
        "dup": "المكرّرات", "empty": "مجلدات فارغة",
        "old": "ملفات قديمة", "junk": "ملفات مؤقتة",
        "export_csv": "CSV", "export_json": "JSON", "export_html": "HTML",
        "toggle_lang": "English", "about": "حول",
        "path_label": "المسار:", "path_placeholder": "اكتب مساراً أو اختر مجلداً / قرصاً...",
        "category": "النوع:", "min_size": "أدنى م.ب:", "max_size": "أقصى م.ب:",
        "top_results": "عدد:", "skip_system": "تخطي مجلدات النظام",
        "cat_all": "كل الأنواع", "cat_video": "فيديو", "cat_image": "صور",
        "cat_audio": "صوتيات", "cat_document": "مستندات",
        "cat_archive": "أرشيفات", "cat_code": "أكواد",
        "cat_executable": "تنفيذية",
        "filter_ext": "الامتدادات:", "filter_min": "أدنى م.ب:",
        "filter_max": "أقصى م.ب:", "filter_age": "أقدم (أيام):",
        "filter_apply": "تطبيق", "filter_reset": "إعادة",
        "age_days": "أقدم من (أيام):",
        "tab_files": "أكبر الملفات", "tab_types": "أنواع الملفات",
        "tab_tool_results": "نتائج الأدوات",
        "col_folder": "المجلد", "col_size": "الحجم", "col_percent": "النسبة",
        "col_count": "الملفات", "col_name": "الاسم",
        "col_parent": "المجلد الحاوي", "col_ext": "الامتداد",
        "col_item": "العنصر", "col_info": "معلومات",
        "header_folders": "  المجلدات الأكثر استهلاكاً",
        "header_files": "  أكبر الملفات",
        "header_types": "  المساحة حسب النوع",
        "header_tool_results": "  نتائج الأدوات",
        "status_ready": "جاهز.",
        "status_scanning": "جاري الفحص: {path}",
        "status_user_scan": "فحص سريع لمجلدات المستخدم ({n} مجلد)...",
        "status_full_scan": "فحص كامل للقرص: {path}",
        "status_progress": "تم فحص {count:,} ملف  |  الحجم: {size}  |  {path}",
        "status_done": "اكتمل  |  الإجمالي: {total}  |  الملفات: {files:,}  |  المجلدات: {folders:,}",
        "status_stopped": "تم الإيقاف",
        "status_cache_loaded": "المحفوظ  |  {time}  |  الإجمالي: {total}",
        "status_tool_working": "جاري التنفيذ: {name}...",
        "msg_warn": "تنبيه", "msg_error": "خطأ",
        "msg_no_path": "الرجاء تحديد مسار.",
        "msg_bad_path": "المسار غير موجود:\n{path}",
        "msg_no_user_dirs": "لم يتم العثور على مجلدات المستخدم.",
        "msg_confirm_delete_title": "تأكيد الحذف",
        "msg_confirm_delete": "حذف {n} عنصر نهائياً؟\n\n{preview}",
        "msg_delete_done": "نتيجة الحذف",
        "msg_delete_ok": "تم حذف {n} عنصر.",
        "msg_delete_fail": "فشل: {n}\n{errors}",
        "msg_scan_error": "فشل الفحص:\n{msg}",
        "msg_not_exist": "العنصر لم يعد موجوداً.",
        "msg_copied": "تم النسخ: {path}",
        "msg_trash_done": "تم نقل {n} عنصر للسلة.",
        "msg_trash_fail": "فشل النقل: {n}\n{errors}",
        "msg_no_drive": "لم يتم تحديد قرص النظام.",
        "msg_no_results": "قم بإجراء فحص أولاً.",
        "msg_exported": "تم التصدير: {path}",
        "trash_unavailable": "سلة المهملات غير متاحة.",
        "copy_path": "نسخ المسار", "trash": "نقل للسلة",
        "delete": "حذف نهائي...",
        "no_ext": "(بدون امتداد)", "other": "أخرى",
        "dup_count": "{n} مجموعة مكرّرة", "empty_count": "{n} مجلد فارغ",
        "old_count": "{n} ملف قديم", "junk_count": "{n} ملف مؤقت",
        "filter_count": "{n} ملف بعد التصفية",
        "no_results_found": "لا توجد نتائج.",
        "dup_group": "مجموعة {i} — {size} × {n}",
        "about_text": (
            "<h3>محلل مساحة القرص</h3>"
            "<p>أداة ثنائية اللغة لفحص استهلاك القرص وإيجاد الملفات الكبيرة "
            "والمكرّرة وتحليل الأنواع.</p>"
            "<p><b>الميزات:</b><br>"
            "• فحص سريع بـ os.scandir<br>"
            "• حفظ مؤقت SQLite<br>"
            "• إيجاد المكرّرات (MD5)<br>"
            "• ملفات فارغة / قديمة / مؤقتة<br>"
            "• تصدير CSV / JSON / HTML</p>"
            "<p style='color:#8ec7ff;font-size:11pt;'>"
            "<b>المطوّر:</b> Craftou عمري 13 حاليا سهيل</p>"
        ),
    },
}


# ============================================================
#  دوال مساعدة
# ============================================================
def human_size(size) -> str:
    if size is None:
        return "-"
    s = float(size)
    if s < 1024:
        return f"{int(s)} B"
    for unit in ("KB", "MB", "GB", "TB"):
        s /= 1024.0
        if s < 1024.0:
            return f"{s:,.2f} {unit}"
    return f"{s:,.2f} PB"


def size_color(size: float) -> QColor:
    gb = 1024 ** 3
    if size >= gb:
        return QColor("#ff5c5c")
    if size >= gb / 10:
        return QColor("#ff9a3c")
    if size >= gb / 100:
        return QColor("#ffd93c")
    return QColor("#9ad1ff")


def bar_color(pct: float) -> QColor:
    if pct >= 50:
        return QColor(200, 60, 60, 160)
    if pct >= 20:
        return QColor(210, 130, 40, 150)
    if pct >= 5:
        return QColor(190, 170, 50, 140)
    return QColor(60, 130, 200, 130)


def resource_path(rel: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def get_app_icon() -> QIcon:
    p = resource_path("icon.ico")
    return QIcon(p) if os.path.isfile(p) else QIcon()


def detect_system_drive() -> str:
    if sys.platform == "win32":
        d = os.environ.get("SystemDrive", "C:")
        if not d.endswith("\\"):
            d += "\\"
        if os.path.isdir(d):
            return d
        if os.path.isdir("C:\\"):
            return "C:\\"
        for l in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            p = f"{l}:\\"
            if os.path.isdir(p):
                return p
        return ""
    return "/"


def get_user_scan_dirs() -> list:
    dirs, seen = [], set()
    for loc in (
        QStandardPaths.StandardLocation.DownloadLocation,
        QStandardPaths.StandardLocation.DocumentsLocation,
        QStandardPaths.StandardLocation.DesktopLocation,
        QStandardPaths.StandardLocation.PicturesLocation,
        QStandardPaths.StandardLocation.MusicLocation,
        QStandardPaths.StandardLocation.MoviesLocation,
    ):
        try:
            p = QStandardPaths.writableLocation(loc)
        except Exception:  # noqa: BLE001
            p = ""
        if p and os.path.isdir(p):
            ap = os.path.abspath(p)
            nc = os.path.normcase(ap)
            if nc not in seen:
                seen.add(nc)
                dirs.append(ap)
    return dirs


def format_age(mtime: float) -> str:
    if not mtime:
        return "-"
    d = (time.time() - mtime) / 86400.0
    if d < 1:
        return "<1d"
    if d < 30:
        return f"{int(d)}d"
    if d < 365:
        return f"{int(d/30)}mo"
    return f"{d/365:.1f}y"


# ============================================================
#  أيقونات مرسومة برمجياً (خطوط بسيطة بدون إيموجي)
# ============================================================
_ICON_CACHE = {}


def make_icon(name: str, size: int = 28, color: str = "#e0e0e0") -> QIcon:
    """يرسم أيقونة خطية بسيطة بالاسم المطلوب ويعيدها كـ QIcon."""
    key = (name, size, color)
    if key in _ICON_CACHE:
        return _ICON_CACHE[key]

    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    c = QColor(color)
    pen = QPen(c)
    pen.setWidthF(max(1.6, size / 14.0))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    S = size / 32.0

    def P(x, y):
        return QPointF(x * S, y * S)

    def R(x, y, w, h):
        return QRectF(x * S, y * S, w * S, h * S)

    if name == "browse":                       # مجلد
        path = QPainterPath()
        path.moveTo(3 * S, 9 * S)
        path.lineTo(3 * S, 25 * S)
        path.lineTo(29 * S, 25 * S)
        path.lineTo(29 * S, 11 * S)
        path.lineTo(15 * S, 11 * S)
        path.lineTo(12 * S, 7 * S)
        path.lineTo(3 * S, 7 * S)
        path.closeSubpath()
        p.drawPath(path)

    elif name == "scan":                       # عدسة مكبّرة
        p.drawEllipse(P(13, 13), 8 * S, 8 * S)
        p.drawLine(P(19, 19), P(27, 27))

    elif name == "stop":                       # مربع توقف
        path = QPainterPath()
        path.addRoundedRect(R(9, 9, 14, 14), 2 * S, 2 * S)
        p.drawPath(path)

    elif name == "refresh":                    # سهم دائري
        p.drawArc(R(7, 7, 18, 18), 60 * 16, 260 * 16)
        ah = QPainterPath()
        ah.moveTo(23 * S, 5 * S)
        ah.lineTo(28 * S, 10 * S)
        ah.lineTo(21 * S, 12 * S)
        ah.closeSubpath()
        p.setBrush(c)
        p.drawPath(ah)
        p.setBrush(Qt.BrushStyle.NoBrush)

    elif name == "user":                       # مستخدم
        p.drawEllipse(P(16, 11), 4 * S, 4 * S)
        path = QPainterPath()
        path.moveTo(7 * S, 26 * S)
        path.arcTo(R(7, 16, 18, 18), 180, -180)
        p.drawPath(path)

    elif name == "drive":                      # قرص صلب
        path = QPainterPath()
        path.addRoundedRect(R(4, 9, 24, 14), 2 * S, 2 * S)
        p.drawPath(path)
        p.drawEllipse(P(22, 16), 2 * S, 2 * S)
        p.drawLine(P(9, 13), P(15, 13))
        p.drawLine(P(9, 19), P(15, 19))

    elif name == "open":                       # مجلد مفتوح مع سهم
        path = QPainterPath()
        path.moveTo(4 * S, 12 * S)
        path.lineTo(4 * S, 26 * S)
        path.lineTo(28 * S, 26 * S)
        path.lineTo(28 * S, 12 * S)
        p.drawPath(path)
        p.drawLine(P(16, 22), P(16, 14))
        ah = QPainterPath()
        ah.moveTo(12 * S, 18 * S)
        ah.lineTo(16 * S, 14 * S)
        ah.lineTo(20 * S, 18 * S)
        p.drawPath(ah)

    elif name == "reveal":                     # هدف
        p.drawEllipse(P(16, 16), 9 * S, 9 * S)
        p.drawEllipse(P(16, 16), 3 * S, 3 * S)
        p.setBrush(c)
        p.drawEllipse(P(16, 16), 1.4 * S, 1.4 * S)
        p.setBrush(Qt.BrushStyle.NoBrush)

    elif name == "dup":                        # نسخ / مكرر
        path = QPainterPath()
        path.addRoundedRect(R(5, 5, 15, 19), 1.5 * S, 1.5 * S)
        p.drawPath(path)
        path = QPainterPath()
        path.addRoundedRect(R(12, 9, 15, 19), 1.5 * S, 1.5 * S)
        p.drawPath(path)

    elif name == "empty_folder":               # مجلد فارغ
        path = QPainterPath()
        path.moveTo(3 * S, 10 * S)
        path.lineTo(3 * S, 25 * S)
        path.lineTo(29 * S, 25 * S)
        path.lineTo(29 * S, 12 * S)
        path.lineTo(15 * S, 12 * S)
        path.lineTo(12 * S, 8 * S)
        path.lineTo(3 * S, 8 * S)
        path.closeSubpath()
        p.drawPath(path)
        pen2 = QPen(c)
        pen2.setWidthF(1.2 * S)
        pen2.setStyle(Qt.PenStyle.DotLine)
        p.setPen(pen2)
        p.drawLine(P(9, 18), P(23, 18))

    elif name == "clock":                      # ساعة
        p.drawEllipse(P(16, 16), 10 * S, 10 * S)
        p.drawLine(P(16, 16), P(16, 10))
        p.drawLine(P(16, 16), P(21, 18))

    elif name == "trash":                      # سلة مهملات
        p.drawLine(P(6, 11), P(26, 11))
        path = QPainterPath()
        path.moveTo(8 * S, 11 * S)
        path.lineTo(10 * S, 27 * S)
        path.lineTo(22 * S, 27 * S)
        path.lineTo(24 * S, 11 * S)
        p.drawPath(path)
        p.drawLine(P(13, 11), P(13, 7))
        p.drawLine(P(19, 11), P(19, 7))
        p.drawLine(P(13, 7), P(19, 7))
        p.drawLine(P(13, 15), P(13, 23))
        p.drawLine(P(19, 15), P(19, 23))

    elif name == "csv":                        # مستند CSV
        path = QPainterPath()
        path.moveTo(7 * S, 4 * S)
        path.lineTo(20 * S, 4 * S)
        path.lineTo(25 * S, 9 * S)
        path.lineTo(25 * S, 28 * S)
        path.lineTo(7 * S, 28 * S)
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(P(20, 4), P(20, 9))
        p.drawLine(P(20, 9), P(25, 9))
        pen2 = QPen(c); pen2.setWidthF(1.6 * S)
        p.setPen(pen2)
        p.drawArc(R(11, 14, 10, 10), 60 * 16, 240 * 16)

    elif name == "json":                       # مستند JSON
        path = QPainterPath()
        path.moveTo(7 * S, 4 * S)
        path.lineTo(20 * S, 4 * S)
        path.lineTo(25 * S, 9 * S)
        path.lineTo(25 * S, 28 * S)
        path.lineTo(7 * S, 28 * S)
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(P(20, 4), P(20, 9))
        p.drawLine(P(20, 9), P(25, 9))
        pen2 = QPen(c); pen2.setWidthF(1.4 * S); pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen2)
        path = QPainterPath()
        path.moveTo(14 * S, 15 * S)
        path.lineTo(11 * S, 17 * S)
        path.lineTo(14 * S, 19 * S)
        path.lineTo(11 * S, 21 * S)
        path.lineTo(14 * S, 23 * S)
        p.drawPath(path)
        path = QPainterPath()
        path.moveTo(20 * S, 15 * S)
        path.lineTo(23 * S, 17 * S)
        path.lineTo(20 * S, 19 * S)
        path.lineTo(23 * S, 21 * S)
        path.lineTo(20 * S, 23 * S)
        p.drawPath(path)

    elif name == "html":                       # كرة أرضية
        p.drawEllipse(P(16, 16), 10 * S, 10 * S)
        p.drawEllipse(P(16, 16), 5 * S, 10 * S)
        p.drawLine(P(6, 16), P(26, 16))
        p.drawLine(P(8, 11), P(24, 11))
        p.drawLine(P(8, 21), P(24, 21))

    elif name == "globe":                      # لغة
        p.drawEllipse(P(16, 16), 10 * S, 10 * S)
        p.drawEllipse(P(16, 16), 5 * S, 10 * S)
        p.drawLine(P(6, 16), P(26, 16))

    elif name == "about":                      # معلومات
        p.drawEllipse(P(16, 16), 11 * S, 11 * S)
        p.setBrush(c)
        p.drawEllipse(P(16, 10), 1.3 * S, 1.3 * S)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawLine(P(16, 14), P(16, 23))

    elif name == "apply":                      # علامة صح
        pen2 = QPen(c); pen2.setWidthF(2.6 * S)
        pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen2.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen2)
        path = QPainterPath()
        path.moveTo(6 * S, 17 * S)
        path.lineTo(13 * S, 24 * S)
        path.lineTo(26 * S, 8 * S)
        p.drawPath(path)

    elif name == "reset":                      # X
        pen2 = QPen(c); pen2.setWidthF(2.6 * S)
        pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen2)
        p.drawLine(P(9, 9), P(23, 23))
        p.drawLine(P(23, 9), P(9, 23))

    elif name == "filter":                     # قمع
        path = QPainterPath()
        path.moveTo(5 * S, 7 * S)
        path.lineTo(27 * S, 7 * S)
        path.lineTo(19 * S, 17 * S)
        path.lineTo(19 * S, 26 * S)
        path.lineTo(13 * S, 23 * S)
        path.lineTo(13 * S, 17 * S)
        path.closeSubpath()
        p.drawPath(path)

    p.end()

    icon = QIcon(pm)
    _ICON_CACHE[key] = icon
    return icon


# ============================================================
#  سلة المهملات
# ============================================================
def _win_trash(path):
    if not _HAS_WINTYPES:
        raise RuntimeError("wintypes unavailable")

    class SF(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND), ("wFunc", wintypes.UINT),
            ("pFrom", wintypes.LPCWSTR), ("pTo", wintypes.LPCWSTR),
            ("fFlags", ctypes.c_uint16),
            ("fAnyOperationsAborted", wintypes.BOOL),
            ("hNameMappings", ctypes.c_void_p),
            ("lpszProgressTitle", wintypes.LPCWSTR),
        ]

    op = SF()
    op.wFunc = 3
    op.pFrom = path + "\0\0"
    op.fFlags = 0x0040 | 0x0010 | 0x0004 | 0x0400
    if ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op)) != 0:
        raise OSError("SHFileOperationW failed")


def move_to_trash(path):
    if _HAS_SEND2TRASH:
        _send2trash(path); return
    if sys.platform == "win32":
        _win_trash(path); return
    raise RuntimeError("Trash not supported")


# ============================================================
#  الحفظ المؤقت
# ============================================================
class ScanCache:
    def __init__(self, db):
        self.db = db
        self._init()

    def _init(self):
        with sqlite3.connect(self.db) as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS scans(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    root TEXT NOT NULL, timestamp REAL NOT NULL,
                    total_size INTEGER NOT NULL, file_count INTEGER NOT NULL,
                    folder_count INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS files(
                    scan_id INTEGER NOT NULL, path TEXT NOT NULL,
                    size INTEGER NOT NULL, mtime REAL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS folders(
                    scan_id INTEGER NOT NULL, path TEXT NOT NULL,
                    size INTEGER NOT NULL, count INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS extensions(
                    scan_id INTEGER NOT NULL, ext TEXT NOT NULL,
                    size INTEGER NOT NULL, count INTEGER NOT NULL);
                CREATE INDEX IF NOT EXISTS ix_s ON scans(root);
                CREATE INDEX IF NOT EXISTS ix_f ON files(scan_id);
                CREATE INDEX IF NOT EXISTS ix_fo ON folders(scan_id);
                CREATE INDEX IF NOT EXISTS ix_e ON extensions(scan_id);
            """)
            try:
                c.execute("ALTER TABLE files ADD COLUMN mtime REAL DEFAULT 0")
            except sqlite3.OperationalError:
                pass

    def save(self, root, total, fcount, files, folders, extensions):
        with sqlite3.connect(self.db) as c:
            c.execute("DELETE FROM scans WHERE root=?", (root,))
            cur = c.execute(
                "INSERT INTO scans(root,timestamp,total_size,file_count,folder_count)"
                " VALUES(?,?,?,?,?)",
                (root, time.time(), int(total), int(fcount), len(folders)))
            sid = cur.lastrowid
            c.executemany("INSERT INTO files(scan_id,path,size,mtime) VALUES(?,?,?,?)",
                          [(sid, p, int(s), float(m)) for p, s, m in files])
            c.executemany("INSERT INTO folders(scan_id,path,size,count) VALUES(?,?,?,?)",
                          [(sid, p, int(s), int(n)) for p, s, n in folders])
            c.executemany("INSERT INTO extensions(scan_id,ext,size,count) VALUES(?,?,?,?)",
                          [(sid, e, int(s), int(n)) for e, s, n in extensions])

    def last_scan(self):
        with sqlite3.connect(self.db) as c:
            r = c.execute("SELECT root,timestamp FROM scans ORDER BY timestamp DESC LIMIT 1").fetchone()
            return {"root": r[0], "timestamp": r[1]} if r else None

    def load(self, root):
        with sqlite3.connect(self.db) as c:
            r = c.execute(
                "SELECT id,timestamp,total_size,file_count FROM scans "
                "WHERE root=? ORDER BY timestamp DESC LIMIT 1", (root,)).fetchone()
            if not r:
                return None
            sid, ts, total, fc = r
            files = c.execute("SELECT path,size,mtime FROM files WHERE scan_id=? ORDER BY size DESC", (sid,)).fetchall()
            folders = c.execute("SELECT path,size,count FROM folders WHERE scan_id=? ORDER BY size DESC", (sid,)).fetchall()
            exts = c.execute("SELECT ext,size,count FROM extensions WHERE scan_id=? ORDER BY size DESC", (sid,)).fetchall()
            return {"root": root, "timestamp": ts, "total": total,
                    "file_count": fc, "files": files,
                    "folders": folders, "extensions": exts}


# ============================================================
#  خيوط العمل
# ============================================================
class ScanWorker(QThread):
    progress = pyqtSignal(str, int, int)
    finished_scan = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, roots, min_size=0, max_size=0, skip_system=True, category="all"):
        super().__init__()
        if isinstance(roots, str):
            roots = [roots]
        norm, seen = [], set()
        for r in roots:
            a = os.path.abspath(r)
            n = os.path.normcase(a)
            if n not in seen:
                seen.add(n); norm.append(a)
        self.roots = norm
        self.min_size = int(min_size)
        self.max_size = int(max_size)
        self.skip_system = bool(skip_system)
        self.category = category or "all"
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        cat = CATEGORIES.get(self.category)
        files, all_files = [], []
        ext_s, ext_c = {}, {}
        total, scanned = 0, 0
        try:
            for root in self.roots:
                if self._stop: break
                stack = [root]
                while stack:
                    if self._stop: break
                    cur = stack.pop()
                    try:
                        with os.scandir(cur) as it:
                            for e in it:
                                if self._stop: break
                                try:
                                    if e.is_dir(follow_symlinks=False):
                                        if self.skip_system and e.name in SKIP_DIR_NAMES:
                                            continue
                                        stack.append(e.path)
                                    elif e.is_file(follow_symlinks=False):
                                        try:
                                            st = e.stat(follow_symlinks=False)
                                        except (PermissionError, OSError):
                                            continue
                                        size = int(st.st_size)
                                        mtime = float(st.st_mtime)
                                        scanned += 1; total += size
                                        ext = os.path.splitext(e.name)[1].lower() or "__no_ext__"
                                        if cat is not None and ext not in cat:
                                            continue
                                        all_files.append((e.path, size, mtime))
                                        ext_s[ext] = ext_s.get(ext, 0) + size
                                        ext_c[ext] = ext_c.get(ext, 0) + 1
                                        if size >= self.min_size and (self.max_size <= 0 or size <= self.max_size):
                                            files.append((e.path, size, mtime))
                                        if scanned % 500 == 0:
                                            self.progress.emit(cur, scanned, total)
                                except (PermissionError, OSError):
                                    continue
                    except (PermissionError, OSError):
                        continue

            if self._stop:
                self.finished_scan.emit(None); return

            fsize, fcount = {}, {}
            roots_sep = [(r, os.path.normcase(r + os.sep)) for r in self.roots]
            roots_exact = {os.path.normcase(r): r for r in self.roots}

            def find_root(fp):
                fn = os.path.normcase(fp)
                for r, rs in roots_sep:
                    if fn.startswith(rs): return r
                return roots_exact.get(fn)

            for fp, fs, _ in all_files:
                rr = find_root(fp)
                if rr is None: continue
                nc = os.path.normcase(rr)
                d = os.path.dirname(fp)
                while True:
                    fsize[d] = fsize.get(d, 0) + fs
                    fcount[d] = fcount.get(d, 0) + 1
                    if os.path.normcase(d) == nc: break
                    p = os.path.dirname(d)
                    if p == d: break
                    d = p

            files.sort(key=lambda x: x[1], reverse=True)
            folders = sorted(((p, s, fcount.get(p, 0)) for p, s in fsize.items()),
                             key=lambda x: x[1], reverse=True)
            extensions = sorted(((e, s, ext_c.get(e, 0)) for e, s in ext_s.items()),
                                key=lambda x: x[1], reverse=True)
            self.finished_scan.emit({
                "roots": self.roots, "files": files, "all_files": all_files,
                "folders": folders, "extensions": extensions,
                "total": total, "scanned": scanned})
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class DuplicateFinderWorker(QThread):
    progress = pyqtSignal(int, int)
    finished_dup = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(self, files):
        super().__init__()
        self.files = list(files)
        self._stop = False

    def stop(self): self._stop = True

    @staticmethod
    def _hash(p, chunk=1024 * 1024):
        h = hashlib.md5()
        try:
            with open(p, "rb") as f:
                while True:
                    b = f.read(chunk)
                    if not b: break
                    h.update(b)
            return h.hexdigest()
        except (OSError, PermissionError):
            return None

    def run(self):
        try:
            by_size = {}
            for p, s, m in self.files:
                if s <= 0: continue
                by_size.setdefault(s, []).append(p)
            cands = [(s, ps) for s, ps in by_size.items() if len(ps) > 1]
            total = sum(len(ps) for _, ps in cands)
            groups, done = [], 0
            for size, paths in cands:
                if self._stop: break
                by_hash = {}
                for p in paths:
                    if self._stop: break
                    done += 1
                    if done % 10 == 0:
                        self.progress.emit(done, total)
                    d = self._hash(p)
                    if d:
                        by_hash.setdefault(d, []).append(p)
                for d, g in by_hash.items():
                    if len(g) > 1:
                        groups.append((size, g))
            groups.sort(key=lambda g: g[0] * (len(g[1]) - 1), reverse=True)
            self.finished_dup.emit(groups)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class EmptyFolderWorker(QThread):
    finished_empty = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(self, roots, skip_system=True):
        super().__init__()
        self.roots = [os.path.abspath(r) for r in roots]
        self.skip_system = skip_system
        self._stop = False

    def stop(self): self._stop = True

    def run(self):
        try:
            empty = []
            for root in self.roots:
                if self._stop: break
                for dp, dn, fn in os.walk(root, topdown=False, onerror=lambda e: None):
                    if self._stop: break
                    if self.skip_system and os.path.basename(dp) in SKIP_DIR_NAMES:
                        continue
                    try:
                        if not os.listdir(dp):
                            empty.append(dp)
                    except (PermissionError, OSError):
                        continue
            self.finished_empty.emit(empty)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


# ============================================================
#  الرسم البياني الدائري
# ============================================================
class PieChart(QWidget):
    COLORS = ["#4a90d9", "#e8743b", "#19a979", "#945ecf", "#13a4b4",
              "#e8b547", "#d94a7c", "#5c8a3a", "#c0504d", "#9c6e3b",
              "#4bacc6", "#f79646", "#8064a2", "#4f81bd", "#a05050"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items, self._total = [], 0
        self.setMinimumSize(300, 300)

    def set_items(self, items):
        self._items = []
        self._total = sum(v for _, v in items) or 1
        for i, (l, v) in enumerate(items):
            self._items.append((l, v, QColor(self.COLORS[i % len(self.COLORS)])))
        self.update()

    def paintEvent(self, e):
        if not self._items: return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        size = max(120, min(w - 40, h // 2 - 10, 220))
        rect = QRect((w - size) // 2, 12, size, size)
        start = 90 * 16
        for _l, v, c in self._items:
            span = int(-v / self._total * 360 * 16)
            p.setBrush(c); p.setPen(QPen(QColor("#111"), 1))
            p.drawPie(rect, start, span)
            start += span
        ly = rect.bottom() + 12; lh = 22
        for l, v, c in self._items[:max(0, (h - ly - 8) // lh)]:
            p.setBrush(c); p.setPen(Qt.PenStyle.NoPen)
            p.drawRect(12, ly + 4, 14, 14)
            pct = v / self._total * 100
            p.setPen(QColor("#dcdcdc"))
            p.drawText(34, ly, w - 46, lh,
                       Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                       f"{l}   —   {human_size(v)}   ({pct:.1f}%)")
            ly += lh
        p.end()


# ============================================================
#  مندوب شريط النسبة
# ============================================================
class PercentBarDelegate(QStyledItemDelegate):
    BAR_ROLE = Qt.ItemDataRole.UserRole + 10
    COLOR_ROLE = Qt.ItemDataRole.UserRole + 11

    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        text = opt.text; opt.text = ""
        w = opt.widget
        style = w.style() if w else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, w)
        pct = index.data(self.BAR_ROLE)
        if pct is not None and pct > 0:
            r = opt.rect.adjusted(2, 3, -2, -3)
            bw = int(r.width() * min(float(pct), 100.0) / 100.0)
            if bw > 0:
                c = index.data(self.COLOR_ROLE) or QColor("#3aa06a")
                if isinstance(c, str): c = QColor(c)
                painter.save()
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(c)
                painter.drawRoundedRect(QRect(r.left(), r.top(), bw, r.height()), 3, 3)
                painter.restore()
        painter.save()
        painter.setPen(opt.palette.color(
            QPalette.ColorRole.HighlightedText
            if opt.state & QStyle.StateFlag.State_Selected
            else QPalette.ColorRole.Text))
        painter.drawText(opt.rect.adjusted(6, 0, -6, 0), opt.displayAlignment, text)
        painter.restore()


# ============================================================
#  عناصر الشريط (Ribbon)
# ============================================================
class RibbonButton(QToolButton):
    """زر بأسلوب Word — أيقونة مرسومة برمجياً فوق/جانب النص."""

    def __init__(self, text="", icon_name="", tooltip="", large=True, parent=None):
        super().__init__(parent)
        self._large = large
        self._icon_name = icon_name
        self._text = text
        self.setToolTip(tooltip or text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAutoRaise(False)

        if large:
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            self.setIconSize(QSize(28, 28))
            self.setMinimumSize(84, 68)
            self.setMaximumWidth(125)
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            self.setObjectName("ribbon_large_btn")
        else:
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            self.setIconSize(QSize(14, 14))
            self.setMinimumHeight(26)
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            self.setObjectName("ribbon_small_btn")

        self._refresh()

    def set_text_icon(self, text, icon_name=None):
        self._text = text
        if icon_name is not None:
            self._icon_name = icon_name
        self.setToolTip(text)
        self._refresh()

    def _refresh(self):
        self.setText(self._text)
        if self._icon_name:
            sz = 28 if self._large else 14
            self.setIcon(make_icon(self._icon_name, sz, "#e0e0e0"))


class RibbonPanel(QFrame):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setObjectName("ribbon_panel")
        self._v = QVBoxLayout(self)
        self._v.setContentsMargins(6, 4, 6, 2)
        self._v.setSpacing(2)

        self._content = QWidget()
        self._content.setObjectName("ribbon_panel_content")
        self._ch = QHBoxLayout(self._content)
        self._ch.setContentsMargins(0, 0, 0, 0)
        self._ch.setSpacing(2)
        self._ch.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._v.addWidget(self._content)

        self._title = QLabel(title)
        self._title.setObjectName("ribbon_panel_title")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._v.addWidget(self._title)

    def set_title(self, t):
        self._title.setText(t)

    def add_widget(self, w):
        self._ch.addWidget(w)

    def add_layout(self, l):
        self._ch.addLayout(l)


class RibbonBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ribbon_bar")
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        self.tab_bar = QTabBar()
        self.tab_bar.setExpanding(False)
        self.tab_bar.setDrawBase(False)
        self.tab_bar.setObjectName("ribbon_tabbar")

        self.stack = QStackedWidget()
        self.stack.setObjectName("ribbon_stack")

        v.addWidget(self.tab_bar)
        v.addWidget(self.stack)
        self.tab_bar.currentChanged.connect(self.stack.setCurrentIndex)

    def add_tab(self, title):
        page = QWidget()
        h = QHBoxLayout(page)
        h.setContentsMargins(6, 6, 6, 6)
        h.setSpacing(2)
        page._layout = h
        self.stack.addWidget(page)
        self.tab_bar.addTab(title)
        return page

    def add_panel(self, page, title):
        if page._layout.count() > 0:
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.VLine)
            sep.setFixedWidth(1)
            sep.setObjectName("ribbon_sep")
            page._layout.addWidget(sep)
        panel = RibbonPanel(title)
        page._layout.addWidget(panel)
        return panel

    def finalize(self, page):
        page._layout.addStretch(1)


# ============================================================
#  النافذة الرئيسية
# ============================================================
class MainWindow(QMainWindow):

    STYLE = """
    QWidget {
        background-color: #000000; color: #dcdcdc;
        font-family: "Segoe UI", "Tahoma", "Arial", sans-serif;
        font-size: 10pt;
    }
    QMainWindow, QDialog { background-color: #000000; }

    /* ============ Ribbon ============ */
    QWidget#ribbon_bar {
        background-color: #000000;
        border-bottom: 1px solid #2a2a2a;
    }
    QTabBar#ribbon_tabbar { background-color: #000000; }
    QTabBar#ribbon_tabbar::tab {
        background-color: transparent; color: #a8a8a8;
        padding: 8px 22px; margin: 0; border: none;
        border-bottom: 2px solid transparent; font-weight: bold;
    }
    QTabBar#ribbon_tabbar::tab:hover {
        background-color: #151515; color: #e0e0e0;
    }
    QTabBar#ribbon_tabbar::tab:selected {
        background-color: #151515; color: #ffffff;
        border-bottom: 2px solid #4a90d9;
    }
    QWidget#ribbon_stack {
        background-color: #0a0a0a;
        border-top: 1px solid #1f1f1f;
    }
    QFrame#ribbon_sep { background-color: #2a2a2a; margin: 6px 2px; }
    QWidget#ribbon_panel, QWidget#ribbon_panel_content { background: transparent; }
    QLabel#ribbon_panel_title { color: #808080; font-size: 8pt; }

    /* ============ Ribbon large buttons ============ */
    QToolButton#ribbon_large_btn {
        background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                                          stop:0 #2b2b2b, stop:1 #151515);
        border: 1px solid #5a5a5a;
        border-radius: 3px;
        padding: 6px 8px;
        color: #e6e6e6;
        font-size: 9pt;
    }
    QToolButton#ribbon_large_btn:hover {
        background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                                          stop:0 #3a3a3a, stop:1 #202020);
        border-color: #8a8a8a;
    }
    QToolButton#ribbon_large_btn:pressed {
        background-color: #0a0a0a;
        border-color: #444444;
    }
    QToolButton#ribbon_large_btn:disabled {
        color: #555555; border-color: #333333; background-color: #101010;
    }
    QToolButton#ribbon_large_btn:focus { border-color: #4a90d9; }

    /* ============ Ribbon small buttons ============ */
    QToolButton#ribbon_small_btn {
        background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                                          stop:0 #2b2b2b, stop:1 #151515);
        border: 1px solid #5a5a5a;
        border-radius: 3px;
        padding: 3px 10px;
        color: #e6e6e6;
        font-size: 9pt;
    }
    QToolButton#ribbon_small_btn:hover {
        background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                                          stop:0 #3a3a3a, stop:1 #202020);
        border-color: #8a8a8a;
    }
    QToolButton#ribbon_small_btn:pressed { background-color: #0a0a0a; }
    QToolButton#ribbon_small_btn:disabled {
        color: #555555; border-color: #333333; background-color: #101010;
    }

    /* ============ Regular buttons ============ */
    QPushButton {
        background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                                          stop:0 #2b2b2b, stop:1 #151515);
        border: 1px solid #5a5a5a; border-radius: 3px;
        padding: 6px 14px; color: #e6e6e6; min-width: 60px;
    }
    QPushButton:hover {
        background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                                          stop:0 #3a3a3a, stop:1 #202020);
        border-color: #8a8a8a;
    }
    QPushButton:pressed {
        background-color: #0a0a0a; border-color: #444;
        padding-top: 7px; padding-bottom: 5px;
    }
    QPushButton:disabled { color:#555; border-color:#333; background-color:#101010; }

    /* ============ Inputs ============ */
    QLineEdit, QSpinBox, QComboBox {
        background-color: #0a0a0a; border: 1px solid #4a4a4a;
        border-radius: 3px; padding: 4px 6px; color: #e6e6e6;
        selection-background-color: #2d4a6b; selection-color: #fff;
    }
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border-color: #4a90d9; }

    QComboBox::drop-down { border: none; width: 20px; }
    QComboBox::down-arrow {
        image: none; border-left: 4px solid transparent;
        border-right: 4px solid transparent; border-top: 5px solid #999;
        margin-right: 6px;
    }
    QComboBox QAbstractItemView {
        background-color: #141414; border: 1px solid #444;
        color: #dcdcdc; selection-background-color: #23405e;
    }

    QCheckBox { spacing: 6px; color: #dcdcdc; }
    QCheckBox::indicator {
        width: 14px; height: 14px; border: 1px solid #5a5a5a;
        border-radius: 2px; background-color: #0a0a0a;
    }
    QCheckBox::indicator:checked { background-color: #4a90d9; border-color: #4a90d9; }

    /* ============ Trees ============ */
    QTreeWidget {
        background-color: #030303; alternate-background-color: #0d0d0d;
        border: 1px solid #3a3a3a; border-radius: 3px;
        outline: none; show-decoration-selected: 1;
    }
    QTreeWidget::item { padding: 3px; border: none; }
    QTreeWidget::item:selected { background-color: #23405e; color: #fff; }
    QTreeWidget::item:hover { background-color: #1a1a1a; }

    QHeaderView::section {
        background-color: #1c1c1c; color: #cfcfcf; padding: 6px;
        border: none; border-right: 1px solid #333;
        border-bottom: 1px solid #333;
    }

    /* ============ Progress ============ */
    QProgressBar {
        border: 1px solid #3a3a3a; border-radius: 3px;
        background-color: #0a0a0a; height: 18px;
        text-align: center; color: #ffffff;
    }
    QProgressBar::chunk {
        background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                                          stop:0 #3aa06a, stop:1 #1f6b45);
    }

    /* ============ Bottom tabs ============ */
    QTabWidget::pane {
        border: 1px solid #3a3a3a; background-color: #030303; top: -1px;
    }
    QTabBar::tab {
        background-color: #141414; color: #bbb;
        padding: 7px 18px; border: 1px solid #3a3a3a;
        border-bottom: none; margin-right: 2px;
    }
    QTabBar::tab:selected {
        background-color: #0a0a0a; color: #fff;
        border-bottom: 1px solid #0a0a0a;
    }
    QTabBar::tab:hover { background-color: #1f1f1f; }

    QSplitter::handle { background-color: #1a1a1a; }
    QSplitter::handle:horizontal { width: 4px; }

    QMenu {
        background-color: #141414; border: 1px solid #444;
        color: #ddd; padding: 4px;
    }
    QMenu::item { padding: 6px 24px; }
    QMenu::item:selected { background-color: #23405e; }
    QMenu::separator { height: 1px; background: #333; margin: 4px 8px; }

    QStatusBar { background-color: #0a0a0a; color: #999; }
    QLabel#header_label { color: #8ec7ff; padding: 2px; font-weight: bold; }

    QScrollBar:vertical { background: #0a0a0a; width: 13px; margin: 0; }
    QScrollBar::handle:vertical { background: #333; min-height: 24px; border-radius: 6px; }
    QScrollBar::handle:vertical:hover { background: #4a4a4a; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

    QScrollBar:horizontal { background: #0a0a0a; height: 13px; margin: 0; }
    QScrollBar::handle:horizontal { background: #333; min-width: 24px; border-radius: 6px; }
    QScrollBar::handle:horizontal:hover { background: #4a4a4a; }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; }
    """

    def __init__(self):
        super().__init__()
        self.lang = "ar"
        self.worker = None
        self.tool_worker = None
        self.current_root = ""
        self.total_size = 0
        self._last_result = None
        self._last_mode = "manual"
        self._last_roots = None
        self._all_files_raw = []

        cache_dir = os.path.join(os.path.expanduser("~"), ".disk_space_analyzer")
        os.makedirs(cache_dir, exist_ok=True)
        self.cache = ScanCache(os.path.join(cache_dir, "cache.db"))

        self._build_ui()
        self.setStyleSheet(self.STYLE)
        self.apply_language(self.lang)
        self.setWindowIcon(get_app_icon())
        self._load_last_cache()

    def t(self, k, **kw):
        s = TR[self.lang].get(k, k)
        return s.format(**kw) if kw else s

    # --------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.ribbon = RibbonBar()
        root.addWidget(self.ribbon)
        self._build_ribbon()

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(10, 8, 10, 8)
        body_layout.setSpacing(6)

        # صف المسار
        row1 = QHBoxLayout(); row1.setSpacing(6)
        self.lbl_path = QLabel(); row1.addWidget(self.lbl_path)
        self.path_edit = QLineEdit()
        self.path_edit.returnPressed.connect(lambda: self.start_scan("manual"))
        row1.addWidget(self.path_edit, 1)
        body_layout.addLayout(row1)

        # شريط التقدم
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        body_layout.addWidget(self.progress)

        # المقسم
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QWidget()
        ll = QVBoxLayout(left); ll.setContentsMargins(0, 0, 0, 0); ll.setSpacing(4)
        self.hdr_folders = QLabel()
        self.hdr_folders.setObjectName("header_label")
        self.hdr_folders.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        ll.addWidget(self.hdr_folders)
        self.folder_tree = QTreeWidget()
        self.folder_tree.setColumnCount(4)
        self.folder_tree.setAlternatingRowColors(True)
        self.folder_tree.setRootIsDecorated(False)
        self.folder_tree.setUniformRowHeights(True)
        self.folder_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.folder_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.folder_tree.customContextMenuRequested.connect(self._show_folder_menu)
        self.folder_tree.itemDoubleClicked.connect(lambda *_: self.open_selected())
        self.folder_tree.setItemDelegateForColumn(2, PercentBarDelegate(self.folder_tree))
        fh = self.folder_tree.header()
        fh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        fh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        fh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed); fh.resizeSection(2, 160)
        fh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        fh.setStretchLastSection(False)
        ll.addWidget(self.folder_tree, 1)
        splitter.addWidget(left)

        self.tabs = QTabWidget()

        tf = QWidget(); vf = QVBoxLayout(tf); vf.setContentsMargins(0, 0, 0, 0); vf.setSpacing(4)
        self.hdr_files = QLabel(); self.hdr_files.setObjectName("header_label")
        self.hdr_files.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold)); vf.addWidget(self.hdr_files)
        self.file_tree = QTreeWidget()
        self.file_tree.setColumnCount(3)
        self.file_tree.setAlternatingRowColors(True)
        self.file_tree.setRootIsDecorated(False)
        self.file_tree.setUniformRowHeights(True)
        self.file_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self._show_file_menu)
        self.file_tree.itemDoubleClicked.connect(lambda *_: self.open_selected())
        fh2 = self.file_tree.header()
        fh2.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        fh2.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        fh2.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.file_tree.setColumnWidth(0, 320)
        vf.addWidget(self.file_tree, 1)
        self.tabs.addTab(tf, "")

        tt = QWidget(); vt = QVBoxLayout(tt); vt.setContentsMargins(0, 0, 0, 0); vt.setSpacing(4)
        self.hdr_types = QLabel(); self.hdr_types.setObjectName("header_label")
        self.hdr_types.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold)); vt.addWidget(self.hdr_types)
        self.pie = PieChart(); vt.addWidget(self.pie, 1)
        self.ext_tree = QTreeWidget()
        self.ext_tree.setColumnCount(4)
        self.ext_tree.setAlternatingRowColors(True)
        self.ext_tree.setRootIsDecorated(False)
        self.ext_tree.setUniformRowHeights(True)
        eh = self.ext_tree.header()
        eh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        eh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        eh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed); eh.resizeSection(2, 140)
        eh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.ext_tree.setItemDelegateForColumn(2, PercentBarDelegate(self.ext_tree))
        vt.addWidget(self.ext_tree, 1)
        self.tabs.addTab(tt, "")

        tr = QWidget(); vr = QVBoxLayout(tr); vr.setContentsMargins(0, 0, 0, 0); vr.setSpacing(4)
        self.hdr_tools = QLabel(); self.hdr_tools.setObjectName("header_label")
        self.hdr_tools.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold)); vr.addWidget(self.hdr_tools)
        self.tools_tree = QTreeWidget()
        self.tools_tree.setColumnCount(3)
        self.tools_tree.setAlternatingRowColors(True)
        self.tools_tree.setRootIsDecorated(True)
        self.tools_tree.setUniformRowHeights(True)
        self.tools_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tools_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tools_tree.customContextMenuRequested.connect(self._show_tools_menu)
        th = self.tools_tree.header()
        th.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        th.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        th.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        vr.addWidget(self.tools_tree, 1)
        self.tabs.addTab(tr, "")

        splitter.addWidget(self.tabs)
        splitter.setSizes([520, 660])
        body_layout.addWidget(splitter, 1)

        root.addWidget(body, 1)
        self.setStatusBar(QStatusBar())

    # --------------------------------------------------------
    def _build_ribbon(self):
        # ============ الرئيسية ============
        home = self.ribbon.add_tab("")

        p = self.ribbon.add_panel(home, "")
        self._btn_browse = RibbonButton("", "browse")
        self._btn_browse.clicked.connect(self.browse_folder)
        p.add_widget(self._btn_browse)

        self._btn_scan = RibbonButton("", "scan")
        self._btn_scan.clicked.connect(lambda: self.start_scan("manual"))
        p.add_widget(self._btn_scan)

        self._btn_stop = RibbonButton("", "stop")
        self._btn_stop.setEnabled(False)
        self._btn_stop.clicked.connect(self.stop_scan)
        p.add_widget(self._btn_stop)

        self._btn_refresh = RibbonButton("", "refresh")
        self._btn_refresh.clicked.connect(self.refresh_scan)
        p.add_widget(self._btn_refresh)

        p = self.ribbon.add_panel(home, "")
        self._btn_user = RibbonButton("", "user")
        self._btn_user.clicked.connect(lambda: self.start_scan("user"))
        p.add_widget(self._btn_user)

        self._btn_full = RibbonButton("", "drive")
        self._btn_full.clicked.connect(lambda: self.start_scan("full"))
        p.add_widget(self._btn_full)

        p = self.ribbon.add_panel(home, "")
        row = QHBoxLayout(); row.setSpacing(4)
        self._lbl_cat = QLabel(); row.addWidget(self._lbl_cat)
        self.cat_combo = QComboBox(); self.cat_combo.setFixedWidth(115)
        for k in ("all", "video", "image", "audio", "document", "archive", "code", "executable"):
            self.cat_combo.addItem("", k)
        row.addWidget(self.cat_combo)
        p.add_layout(row)

        row2 = QHBoxLayout(); row2.setSpacing(4)
        self._lbl_min = QLabel(); row2.addWidget(self._lbl_min)
        self.min_size_spin = QSpinBox(); self.min_size_spin.setRange(0, 1_000_000)
        self.min_size_spin.setValue(10); self.min_size_spin.setFixedWidth(70)
        row2.addWidget(self.min_size_spin)
        self._lbl_max = QLabel(); row2.addWidget(self._lbl_max)
        self.max_size_spin = QSpinBox(); self.max_size_spin.setRange(0, 1_000_000)
        self.max_size_spin.setValue(0); self.max_size_spin.setFixedWidth(70)
        row2.addWidget(self.max_size_spin)
        p.add_layout(row2)

        row3 = QHBoxLayout(); row3.setSpacing(4)
        self._lbl_top = QLabel(); row3.addWidget(self._lbl_top)
        self.top_spin = QSpinBox(); self.top_spin.setRange(20, 200_000)
        self.top_spin.setValue(300); self.top_spin.setFixedWidth(80)
        row3.addWidget(self.top_spin)
        p.add_layout(row3)

        p = self.ribbon.add_panel(home, "")
        self._btn_open = RibbonButton("", "open")
        self._btn_open.clicked.connect(self.open_selected)
        p.add_widget(self._btn_open)

        self._btn_reveal = RibbonButton("", "reveal")
        self._btn_reveal.clicked.connect(self.locate_selected)
        p.add_widget(self._btn_reveal)

        self.ribbon.finalize(home)

        # ============ الأدوات ============
        tools = self.ribbon.add_tab("")

        p = self.ribbon.add_panel(tools, "")
        self._btn_dup = RibbonButton("", "dup")
        self._btn_dup.clicked.connect(self._find_duplicates)
        p.add_widget(self._btn_dup)

        self._btn_empty = RibbonButton("", "empty_folder")
        self._btn_empty.clicked.connect(self._find_empty_folders)
        p.add_widget(self._btn_empty)

        self._btn_old = RibbonButton("", "clock")
        self._btn_old.clicked.connect(self._find_old_files)
        p.add_widget(self._btn_old)

        self._btn_junk = RibbonButton("", "trash")
        self._btn_junk.clicked.connect(self._find_junk_files)
        p.add_widget(self._btn_junk)

        age_col = QVBoxLayout(); age_col.setSpacing(2)
        self._lbl_age = QLabel(); age_col.addWidget(self._lbl_age)
        self.age_spin = QSpinBox(); self.age_spin.setRange(30, 36500)
        self.age_spin.setValue(365); self.age_spin.setFixedWidth(90)
        age_col.addWidget(self.age_spin)
        p.add_layout(age_col)

        p = self.ribbon.add_panel(tools, "")
        row_ext = QHBoxLayout(); row_ext.setSpacing(4)
        self._lbl_filter_ext = QLabel(); row_ext.addWidget(self._lbl_filter_ext)
        self.filter_ext_edit = QLineEdit(); self.filter_ext_edit.setFixedWidth(170)
        self.filter_ext_edit.setPlaceholderText(".mp4,.mkv,.avi")
        row_ext.addWidget(self.filter_ext_edit)
        p.add_layout(row_ext)

        row_fr2 = QHBoxLayout(); row_fr2.setSpacing(4)
        self._lbl_filter_min = QLabel(); row_fr2.addWidget(self._lbl_filter_min)
        self.filter_min_spin = QSpinBox(); self.filter_min_spin.setRange(0, 1_000_000)
        self.filter_min_spin.setFixedWidth(70); row_fr2.addWidget(self.filter_min_spin)
        self._lbl_filter_max = QLabel(); row_fr2.addWidget(self._lbl_filter_max)
        self.filter_max_spin = QSpinBox(); self.filter_max_spin.setRange(0, 1_000_000)
        self.filter_max_spin.setFixedWidth(70); row_fr2.addWidget(self.filter_max_spin)
        self._lbl_filter_age = QLabel(); row_fr2.addWidget(self._lbl_filter_age)
        self.filter_age_spin = QSpinBox(); self.filter_age_spin.setRange(0, 36500)
        self.filter_age_spin.setFixedWidth(70); row_fr2.addWidget(self.filter_age_spin)
        p.add_layout(row_fr2)

        row_fr3 = QHBoxLayout(); row_fr3.setSpacing(4)
        self._btn_fapply = RibbonButton("", "apply", large=False)
        self._btn_fapply.clicked.connect(self._apply_filter)
        row_fr3.addWidget(self._btn_fapply)
        self._btn_freset = RibbonButton("", "reset", large=False)
        self._btn_freset.clicked.connect(self._reset_filter)
        row_fr3.addWidget(self._btn_freset)
        row_fr3.addStretch(1)
        p.add_layout(row_fr3)

        p = self.ribbon.add_panel(tools, "")
        self._btn_csv = RibbonButton("", "csv")
        self._btn_csv.clicked.connect(self._export_csv)
        p.add_widget(self._btn_csv)

        self._btn_json = RibbonButton("", "json")
        self._btn_json.clicked.connect(self._export_json)
        p.add_widget(self._btn_json)

        self._btn_html = RibbonButton("", "html")
        self._btn_html.clicked.connect(self._export_html)
        p.add_widget(self._btn_html)

        self.ribbon.finalize(tools)

        # ============ العرض ============
        view = self.ribbon.add_tab("")

        p = self.ribbon.add_panel(view, "")
        self._btn_lang = RibbonButton("", "globe")
        self._btn_lang.clicked.connect(self.toggle_language)
        p.add_widget(self._btn_lang)

        p = self.ribbon.add_panel(view, "")
        opt_col = QVBoxLayout(); opt_col.setSpacing(4)
        self.skip_check = QCheckBox(); self.skip_check.setChecked(True)
        opt_col.addWidget(self.skip_check)
        p.add_layout(opt_col)

        p = self.ribbon.add_panel(view, "")
        self._btn_about = RibbonButton("", "about")
        self._btn_about.clicked.connect(self._show_about)
        p.add_widget(self._btn_about)

        self.ribbon.finalize(view)

    # --------------------------------------------------------
    def apply_language(self, lang: str):
        self.lang = lang
        QApplication.instance().setLayoutDirection(
            Qt.LayoutDirection.RightToLeft if lang == "ar"
            else Qt.LayoutDirection.LeftToRight)

        self.setWindowTitle(self.t("app_title"))

        self.ribbon.tab_bar.setTabText(0, self.t("ribbon_home"))
        self.ribbon.tab_bar.setTabText(1, self.t("ribbon_tools"))
        self.ribbon.tab_bar.setTabText(2, self.t("ribbon_view"))

        for page_idx, titles in (
            (0, ["grp_scan", "grp_quick", "grp_filters", "grp_actions"]),
            (1, ["grp_analysis", "grp_filter_results", "grp_export"]),
            (2, ["grp_language", "grp_options", "grp_info"]),
        ):
            page = self.ribbon.stack.widget(page_idx)
            panels = page.findChildren(RibbonPanel)
            for i, pnl in enumerate(panels):
                if i < len(titles):
                    pnl.set_title(self.t(titles[i]))

        self._btn_browse.set_text_icon(self.t("browse"))
        self._btn_scan.set_text_icon(self.t("scan"))
        self._btn_stop.set_text_icon(self.t("stop"))
        self._btn_refresh.set_text_icon(self.t("refresh"))
        self._btn_user.set_text_icon(self.t("user_scan"))
        self._btn_full.set_text_icon(self.t("full_scan"))
        self._btn_open.set_text_icon(self.t("open"))
        self._btn_reveal.set_text_icon(self.t("reveal"))
        self._btn_dup.set_text_icon(self.t("dup"))
        self._btn_empty.set_text_icon(self.t("empty"))
        self._btn_old.set_text_icon(self.t("old"))
        self._btn_junk.set_text_icon(self.t("junk"))
        self._btn_csv.set_text_icon(self.t("export_csv"))
        self._btn_json.set_text_icon(self.t("export_json"))
        self._btn_html.set_text_icon(self.t("export_html"))
        self._btn_lang.set_text_icon(self.t("toggle_lang"))
        self._btn_about.set_text_icon(self.t("about"))
        self._btn_fapply.set_text_icon(self.t("filter_apply"))
        self._btn_freset.set_text_icon(self.t("filter_reset"))

        self.lbl_path.setText(self.t("path_label"))
        self.path_edit.setPlaceholderText(self.t("path_placeholder"))
        self._lbl_cat.setText(self.t("category"))
        self._lbl_min.setText(self.t("min_size"))
        self._lbl_max.setText(self.t("max_size"))
        self._lbl_top.setText(self.t("top_results"))
        self._lbl_age.setText(self.t("age_days"))
        self._lbl_filter_ext.setText(self.t("filter_ext"))
        self._lbl_filter_min.setText(self.t("filter_min"))
        self._lbl_filter_max.setText(self.t("filter_max"))
        self._lbl_filter_age.setText(self.t("filter_age"))
        self.skip_check.setText(self.t("skip_system"))

        for i, k in enumerate(("all", "video", "image", "audio", "document",
                                "archive", "code", "executable")):
            self.cat_combo.setItemText(i, self.t(f"cat_{k}"))

        self.hdr_folders.setText(self.t("header_folders"))
        self.hdr_files.setText(self.t("header_files"))
        self.hdr_types.setText(self.t("header_types"))
        self.hdr_tools.setText(self.t("header_tool_results"))

        self.folder_tree.setHeaderLabels([
            self.t("col_folder"), self.t("col_size"),
            self.t("col_percent"), self.t("col_count")])
        self.file_tree.setHeaderLabels([
            self.t("col_name"), self.t("col_size"), self.t("col_parent")])
        self.ext_tree.setHeaderLabels([
            self.t("col_ext"), self.t("col_size"),
            self.t("col_percent"), self.t("col_count")])
        self.tools_tree.setHeaderLabels([
            self.t("col_item"), self.t("col_size"), self.t("col_info")])

        self.tabs.setTabText(0, self.t("tab_files"))
        self.tabs.setTabText(1, self.t("tab_types"))
        self.tabs.setTabText(2, self.t("tab_tool_results"))

        if self._last_result is not None:
            self._display_results(self._last_result, keep_status=True)
        if not self.statusBar().currentMessage() or self.current_root == "":
            self.statusBar().showMessage(self.t("status_ready"))

    def toggle_language(self):
        self.apply_language("en" if self.lang == "ar" else "ar")

    # --------------------------------------------------------
    def browse_folder(self):
        start = self.path_edit.text().strip() or os.path.expanduser("~")
        if not os.path.isdir(start):
            start = os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(
            self, self.t("browse"), start,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks)
        if folder:
            self.path_edit.setText(os.path.abspath(folder))

    def start_scan(self, mode="manual"):
        if self.worker is not None and self.worker.isRunning():
            return

        if mode == "user":
            roots = get_user_scan_dirs()
            if not roots:
                QMessageBox.warning(self, self.t("msg_warn"), self.t("msg_no_user_dirs")); return
            cache_key = USER_SCAN_KEY
        elif mode == "full":
            drive = detect_system_drive()
            if not drive or not os.path.isdir(drive):
                QMessageBox.warning(self, self.t("msg_warn"), self.t("msg_no_drive")); return
            roots = [drive]; cache_key = drive
            self.path_edit.setText(drive)
        else:
            raw = self.path_edit.text().strip().strip('"').strip("'")
            if not raw:
                QMessageBox.warning(self, self.t("msg_warn"), self.t("msg_no_path")); return
            path = os.path.abspath(os.path.expanduser(raw))
            if not os.path.isdir(path):
                QMessageBox.warning(self, self.t("msg_warn"),
                                    self.t("msg_bad_path", path=path)); return
            roots = [path]; cache_key = path
            self.path_edit.setText(path)

        self.current_root = cache_key
        self._last_mode = mode
        self._last_roots = list(roots)

        self.folder_tree.clear(); self.file_tree.clear()
        self.ext_tree.clear(); self.tools_tree.clear()
        self.pie.set_items([])
        self.total_size = 0
        self._all_files_raw = []
        self.progress.setRange(0, 0)

        min_b = int(self.min_size_spin.value()) * 1024 * 1024
        max_b = int(self.max_size_spin.value()) * 1024 * 1024
        cat = self.cat_combo.currentData() or "all"

        self.worker = ScanWorker(roots, min_b, max_b,
                                 skip_system=self.skip_check.isChecked(),
                                 category=cat)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_scan.connect(self._on_scan_finished)
        self.worker.failed.connect(self._on_scan_failed)
        self.worker.finished.connect(self._on_worker_finished)

        self._set_scanning(True)

        if mode == "user":
            self.statusBar().showMessage(self.t("status_user_scan", n=len(roots)))
        elif mode == "full":
            self.statusBar().showMessage(self.t("status_full_scan", path=roots[0]))
        else:
            self.statusBar().showMessage(self.t("status_scanning", path=roots[0]))
        self.worker.start()

    def refresh_scan(self):
        self.start_scan(self._last_mode or "manual")

    def stop_scan(self):
        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()
            self.statusBar().showMessage(self.t("status_stopped"))
            self._btn_stop.setEnabled(False)

    def _set_scanning(self, scanning):
        for b in (self._btn_scan, self._btn_browse, self._btn_refresh,
                  self._btn_user, self._btn_full):
            b.setEnabled(not scanning)
        for w in (self.min_size_spin, self.max_size_spin, self.top_spin,
                  self.skip_check, self.path_edit, self.cat_combo):
            w.setEnabled(not scanning)
        self._btn_stop.setEnabled(scanning)

    def _on_progress(self, path, scanned, total):
        short = path if len(path) <= 70 else "..." + path[-67:]
        self.statusBar().showMessage(
            self.t("status_progress", count=scanned,
                   size=human_size(total), path=short))

    def _on_scan_finished(self, result):
        if result is None:
            self.statusBar().showMessage(self.t("status_stopped")); return
        self._last_result = result
        self._all_files_raw = list(result.get("all_files", []))
        self._display_results(result)
        try:
            self.cache.save(root=self.current_root,
                            total_size=result["total"],
                            file_count=result["scanned"],
                            files=result["files"],
                            folders=result["folders"],
                            extensions=result["extensions"])
        except Exception as exc:  # noqa: BLE001
            print(f"[cache] {exc}")

    def _on_scan_failed(self, msg):
        QMessageBox.critical(self, self.t("msg_error"),
                             self.t("msg_scan_error", msg=msg))
        self.statusBar().showMessage(self.t("msg_error"))

    def _on_worker_finished(self):
        self._set_scanning(False)
        if self.progress.maximum() == 0:
            self.progress.setRange(0, 100); self.progress.setValue(0)

    # --------------------------------------------------------
    def _display_results(self, result, keep_status=False):
        total = result["total"] or 1
        top = int(self.top_spin.value())
        files = result["files"]; folders = result["folders"]
        extensions = result["extensions"]

        self.folder_tree.setUpdatesEnabled(False); self.folder_tree.clear()
        for path, size, count in folders[:top]:
            pct = size / total * 100.0
            it = QTreeWidgetItem([
                ltr(path), ltr(human_size(size)),
                ltr(f"{pct:.2f}%"), ltr(f"{count:,}")])
            it.setData(0, Qt.ItemDataRole.UserRole, path)
            it.setToolTip(0, path)
            it.setTextAlignment(1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            it.setTextAlignment(2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            it.setTextAlignment(3, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            it.setForeground(1, QBrush(size_color(size)))
            it.setData(2, PercentBarDelegate.BAR_ROLE, pct)
            it.setData(2, PercentBarDelegate.COLOR_ROLE, bar_color(pct))
            self.folder_tree.addTopLevelItem(it)
        self.folder_tree.setUpdatesEnabled(True)

        self.file_tree.setUpdatesEnabled(False); self.file_tree.clear()
        for row in files[:top]:
            fpath, size = row[0], row[1]
            it = QTreeWidgetItem([
                ltr(os.path.basename(fpath)), ltr(human_size(size)),
                ltr(os.path.dirname(fpath))])
            it.setData(0, Qt.ItemDataRole.UserRole, fpath)
            it.setToolTip(0, fpath)
            it.setToolTip(2, os.path.dirname(fpath))
            it.setTextAlignment(1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            it.setForeground(1, QBrush(size_color(size)))
            self.file_tree.addTopLevelItem(it)
        self.file_tree.setUpdatesEnabled(True)

        self.ext_tree.setUpdatesEnabled(False); self.ext_tree.clear()
        for ext, size, count in extensions[:top]:
            label = self.t("no_ext") if ext == "__no_ext__" else ext
            pct = size / total * 100.0
            it = QTreeWidgetItem([
                ltr(label), ltr(human_size(size)),
                ltr(f"{pct:.2f}%"), ltr(f"{count:,}")])
            it.setTextAlignment(1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            it.setTextAlignment(2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            it.setTextAlignment(3, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            it.setForeground(1, QBrush(size_color(size)))
            it.setData(2, PercentBarDelegate.BAR_ROLE, pct)
            it.setData(2, PercentBarDelegate.COLOR_ROLE, bar_color(pct))
            self.ext_tree.addTopLevelItem(it)
        self.ext_tree.setUpdatesEnabled(True)

        top_n = 12
        chart = []
        for ext, size, _ in extensions[:top_n]:
            chart.append((self.t("no_ext") if ext == "__no_ext__" else ext, size))
        rest = sum(s for _, s, _ in extensions[top_n:])
        if rest > 0:
            chart.append((self.t("other"), rest))
        self.pie.set_items(chart)

        self.progress.setRange(0, 100); self.progress.setValue(100)

        if not keep_status:
            ts = result.get("timestamp")
            if ts:
                when = time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))
                self.statusBar().showMessage(
                    self.t("status_cache_loaded", time=when, total=human_size(total)))
            else:
                self.statusBar().showMessage(
                    self.t("status_done", total=human_size(total),
                           files=result.get("scanned", len(files)),
                           folders=len(folders)))

    def _load_last_cache(self):
        last = self.cache.last_scan()
        if not last:
            self.statusBar().showMessage(self.t("status_ready")); return
        result = self.cache.load(last["root"])
        if not result:
            self.statusBar().showMessage(self.t("status_ready")); return

        result["files"] = [(p, s, m) for p, s, m in result["files"]]
        result["all_files"] = list(result["files"])
        result["folders"] = [(p, s, c) for p, s, c in result["folders"]]
        result["extensions"] = [(e, s, c) for e, s, c in result["extensions"]]
        result["scanned"] = result.get("file_count", len(result["files"]))
        result["timestamp"] = last["timestamp"]

        self.current_root = last["root"]
        if last["root"] == USER_SCAN_KEY:
            self._last_mode = "user"
        elif last["root"] and os.path.isdir(last["root"]) and len(last["root"]) <= 4:
            self._last_mode = "full"; self.path_edit.setText(last["root"])
        else:
            self._last_mode = "manual"; self.path_edit.setText(last["root"])

        self._last_result = result
        self._all_files_raw = list(result["all_files"])
        self._display_results(result)

    # --------------------------------------------------------
    def _selected_path(self):
        for tree in (self.file_tree, self.folder_tree, self.ext_tree, self.tools_tree):
            items = tree.selectedItems()
            if items:
                return items[0].data(0, Qt.ItemDataRole.UserRole)
        return None

    def _all_selected_paths(self):
        paths = []
        for tree in (self.file_tree, self.folder_tree, self.tools_tree):
            for it in tree.selectedItems():
                p = it.data(0, Qt.ItemDataRole.UserRole)
                if p and p not in paths:
                    paths.append(p)
        return paths

    def open_selected(self):
        p = self._selected_path()
        if not p: return
        if not os.path.exists(p):
            QMessageBox.warning(self, self.t("msg_warn"), self.t("msg_not_exist")); return
        QDesktopServices.openUrl(QUrl.fromLocalFile(p))

    def locate_selected(self):
        p = self._selected_path()
        if not p: return
        t = p if os.path.isdir(p) else os.path.dirname(p)
        if os.path.isdir(t):
            QDesktopServices.openUrl(QUrl.fromLocalFile(t))

    def copy_path(self):
        p = self._selected_path()
        if not p: return
        QApplication.clipboard().setText(p)
        self.statusBar().showMessage(self.t("msg_copied", path=p), 4000)

    def delete_selected(self):
        paths = [p for p in self._all_selected_paths() if os.path.exists(p)]
        if not paths: return
        preview = "\n".join(paths[:10])
        if len(paths) > 10: preview += f"\n... (+{len(paths)-10})"
        if QMessageBox.question(
            self, self.t("msg_confirm_delete_title"),
            self.t("msg_confirm_delete", n=len(paths), preview=preview),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        errs, done = [], 0
        for p in paths:
            try:
                if os.path.isdir(p): os.rmdir(p)
                else: os.remove(p)
                done += 1
            except OSError as e:
                errs.append(f"{p}\n   -> {e}")
        m = self.t("msg_delete_ok", n=done)
        if errs:
            m += "\n\n" + self.t("msg_delete_fail", n=len(errs),
                                  errors="\n".join(errs[:8]))
        QMessageBox.information(self, self.t("msg_delete_done"), m)

    def trash_selected(self):
        paths = [p for p in self._all_selected_paths() if os.path.exists(p)]
        if not paths: return
        errs, moved = [], 0
        for p in paths:
            try:
                move_to_trash(p); moved += 1
            except Exception as e:  # noqa: BLE001
                errs.append(f"{p}\n   -> {e}")
        if moved == 0 and errs:
            QMessageBox.warning(self, self.t("msg_warn"), self.t("trash_unavailable")); return
        m = self.t("msg_trash_done", n=moved)
        if errs:
            m += "\n\n" + self.t("msg_trash_fail", n=len(errs),
                                  errors="\n".join(errs[:8]))
        QMessageBox.information(self, self.t("msg_delete_done"), m)

    def _make_menu(self):
        m = QMenu(self)
        m.addAction(self.t("open"), self.open_selected)
        m.addAction(self.t("reveal"), self.locate_selected)
        m.addSeparator()
        m.addAction(self.t("copy_path"), self.copy_path)
        m.addSeparator()
        m.addAction(self.t("trash"), self.trash_selected)
        m.addAction(self.t("delete"), self.delete_selected)
        return m

    def _show_folder_menu(self, pos):
        it = self.folder_tree.itemAt(pos)
        if it is not None:
            self.folder_tree.setCurrentItem(it)
            self._make_menu().exec(self.folder_tree.viewport().mapToGlobal(pos))

    def _show_file_menu(self, pos):
        it = self.file_tree.itemAt(pos)
        if it is not None:
            self.file_tree.setCurrentItem(it)
            self._make_menu().exec(self.file_tree.viewport().mapToGlobal(pos))

    def _show_tools_menu(self, pos):
        it = self.tools_tree.itemAt(pos)
        if it is not None:
            self.tools_tree.setCurrentItem(it)
            self._make_menu().exec(self.tools_tree.viewport().mapToGlobal(pos))

    # --------------------------------------------------------
    def _set_tools_busy(self, busy):
        for b in (self._btn_dup, self._btn_empty, self._btn_old, self._btn_junk,
                  self._btn_fapply, self._btn_freset,
                  self._btn_csv, self._btn_json, self._btn_html):
            b.setEnabled(not busy)

    def _apply_filter(self):
        if not self._all_files_raw:
            QMessageBox.information(self, self.t("msg_warn"), self.t("msg_no_results")); return
        ext_text = self.filter_ext_edit.text().strip().lower()
        wanted = None
        if ext_text:
            wanted = set()
            for tok in ext_text.replace(";", ",").split(","):
                tok = tok.strip()
                if not tok: continue
                if not tok.startswith("."): tok = "." + tok
                wanted.add(tok)

        fmin = self.filter_min_spin.value() * 1024 * 1024
        fmax = self.filter_max_spin.value() * 1024 * 1024
        age_days = self.filter_age_spin.value()
        cutoff = time.time() - age_days * 86400 if age_days > 0 else 0

        filtered = []
        for p, s, m in self._all_files_raw:
            if s < fmin: continue
            if fmax > 0 and s > fmax: continue
            if cutoff and m >= cutoff: continue
            if wanted is not None:
                ext = os.path.splitext(p)[1].lower() or "__no_ext__"
                if ext not in wanted: continue
            filtered.append((p, s, m))
        filtered.sort(key=lambda x: x[1], reverse=True)

        self.file_tree.setUpdatesEnabled(False); self.file_tree.clear()
        for p, s, _ in filtered[:int(self.top_spin.value())]:
            it = QTreeWidgetItem([
                ltr(os.path.basename(p)), ltr(human_size(s)),
                ltr(os.path.dirname(p))])
            it.setData(0, Qt.ItemDataRole.UserRole, p)
            it.setTextAlignment(1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            it.setForeground(1, QBrush(size_color(s)))
            self.file_tree.addTopLevelItem(it)
        self.file_tree.setUpdatesEnabled(True)
        self.tabs.setCurrentIndex(0)
        self.statusBar().showMessage(self.t("filter_count", n=len(filtered)))

    def _reset_filter(self):
        self.filter_ext_edit.clear()
        self.filter_min_spin.setValue(0)
        self.filter_max_spin.setValue(0)
        self.filter_age_spin.setValue(0)
        if self._last_result is not None:
            self._display_results(self._last_result, keep_status=True)

    def _find_duplicates(self):
        if not self._all_files_raw:
            QMessageBox.information(self, self.t("msg_warn"), self.t("msg_no_results")); return
        if self.tool_worker is not None and self.tool_worker.isRunning(): return
        self.tools_tree.clear()
        self._set_tools_busy(True)
        self.progress.setRange(0, 0)
        self.statusBar().showMessage(self.t("status_tool_working", name=self.t("dup")))
        self.tool_worker = DuplicateFinderWorker(self._all_files_raw)
        self.tool_worker.progress.connect(lambda i, t: self.progress.setFormat(f"{i}/{t}"))
        self.tool_worker.finished_dup.connect(self._on_duplicates_ready)
        self.tool_worker.failed.connect(
            lambda msg: QMessageBox.critical(self, self.t("msg_error"), msg))
        self.tool_worker.finished.connect(self._on_tool_finished)
        self.tool_worker.start()

    def _on_duplicates_ready(self, groups):
        self.tools_tree.clear()
        for i, (size, paths) in enumerate(groups, 1):
            h = QTreeWidgetItem([
                ltr(self.t("dup_group", i=i, size=human_size(size), n=len(paths))),
                ltr(human_size(size * (len(paths) - 1))),
                ltr(f"x{len(paths)}")])
            h.setFirstColumnSpanned(True)
            h.setForeground(1, QBrush(QColor("#ff9a3c")))
            self.tools_tree.addTopLevelItem(h)
            for p in paths:
                c = QTreeWidgetItem([ltr(p), ltr(human_size(size)), ""])
                c.setData(0, Qt.ItemDataRole.UserRole, p)
                h.addChild(c)
            h.setExpanded(True)
        self.tabs.setCurrentIndex(2)
        self.statusBar().showMessage(
            self.t("dup_count", n=len(groups)) if groups else self.t("no_results_found"))

    def _find_empty_folders(self):
        if not self._last_roots:
            QMessageBox.information(self, self.t("msg_warn"), self.t("msg_no_results")); return
        if self.tool_worker is not None and self.tool_worker.isRunning(): return
        self.tools_tree.clear()
        self._set_tools_busy(True)
        self.progress.setRange(0, 0)
        self.statusBar().showMessage(self.t("status_tool_working", name=self.t("empty")))
        self.tool_worker = EmptyFolderWorker(self._last_roots,
                                              skip_system=self.skip_check.isChecked())
        self.tool_worker.finished_empty.connect(self._on_empty_ready)
        self.tool_worker.failed.connect(
            lambda msg: QMessageBox.critical(self, self.t("msg_error"), msg))
        self.tool_worker.finished.connect(self._on_tool_finished)
        self.tool_worker.start()

    def _on_empty_ready(self, folders):
        self.tools_tree.clear()
        for p in folders:
            it = QTreeWidgetItem([ltr(p), "", ""])
            it.setData(0, Qt.ItemDataRole.UserRole, p)
            it.setForeground(0, QBrush(QColor("#9ad1ff")))
            self.tools_tree.addTopLevelItem(it)
        self.tabs.setCurrentIndex(2)
        self.statusBar().showMessage(
            self.t("empty_count", n=len(folders)) if folders else self.t("no_results_found"))

    def _find_junk_files(self):
        if not self._all_files_raw:
            QMessageBox.information(self, self.t("msg_warn"), self.t("msg_no_results")); return
        self.tools_tree.clear()
        rows = [(p, s, m) for p, s, m in self._all_files_raw
                if os.path.splitext(p)[1].lower() in JUNK_EXTS]
        rows.sort(key=lambda x: x[1], reverse=True)
        total_sz = 0
        for p, s, m in rows:
            it = QTreeWidgetItem([ltr(p), ltr(human_size(s)), ltr(format_age(m))])
            it.setData(0, Qt.ItemDataRole.UserRole, p)
            it.setForeground(1, QBrush(size_color(s)))
            self.tools_tree.addTopLevelItem(it)
            total_sz += s
        self.tabs.setCurrentIndex(2)
        self.statusBar().showMessage(
            self.t("junk_count", n=len(rows)) + f"  —  {human_size(total_sz)}"
            if rows else self.t("no_results_found"))

    def _find_old_files(self):
        if not self._all_files_raw:
            QMessageBox.information(self, self.t("msg_warn"), self.t("msg_no_results")); return
        cutoff = time.time() - int(self.age_spin.value()) * 86400
        self.tools_tree.clear()
        rows = [(p, s, m) for p, s, m in self._all_files_raw if m and m < cutoff]
        rows.sort(key=lambda x: x[1], reverse=True)
        for p, s, m in rows:
            it = QTreeWidgetItem([ltr(p), ltr(human_size(s)), ltr(format_age(m))])
            it.setData(0, Qt.ItemDataRole.UserRole, p)
            it.setForeground(1, QBrush(size_color(s)))
            self.tools_tree.addTopLevelItem(it)
        self.tabs.setCurrentIndex(2)
        self.statusBar().showMessage(
            self.t("old_count", n=len(rows)) if rows else self.t("no_results_found"))

    def _on_tool_finished(self):
        self._set_tools_busy(False)
        self.progress.setRange(0, 100); self.progress.setValue(100)
        self.progress.setFormat("%p%")

    # --------------------------------------------------------
    def _ensure_results(self):
        if self._last_result is None:
            QMessageBox.information(self, self.t("msg_warn"), self.t("msg_no_results"))
            return False
        return True

    def _export_csv(self):
        if not self._ensure_results(): return
        path, _ = QFileDialog.getSaveFileName(self, self.t("export_csv"),
                                               "report.csv", "CSV (*.csv)")
        if not path: return
        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f)
                w.writerow(["Path", "Size (B)", "Size", "Modified", "Ext", "Folder"])
                for row in self._last_result["files"]:
                    p, s = row[0], row[1]
                    m = row[2] if len(row) > 2 else 0
                    w.writerow([p, s, human_size(s),
                                time.strftime("%Y-%m-%d %H:%M",
                                              time.localtime(m)) if m else "",
                                os.path.splitext(p)[1].lower(),
                                os.path.dirname(p)])
            self.statusBar().showMessage(self.t("msg_exported", path=path), 5000)
        except OSError as e:
            QMessageBox.critical(self, self.t("msg_error"), str(e))

    def _export_json(self):
        if not self._ensure_results(): return
        path, _ = QFileDialog.getSaveFileName(self, self.t("export_json"),
                                               "report.json", "JSON (*.json)")
        if not path: return
        r = self._last_result
        data = {
            "root": r.get("root", ""),
            "timestamp": r.get("timestamp") or time.time(),
            "total_size": r["total"],
            "file_count": r.get("scanned", len(r["files"])),
            "files": [{"path": row[0], "size": row[1],
                       "mtime": row[2] if len(row) > 2 else 0}
                      for row in r["files"]],
            "folders": [{"path": p, "size": s, "count": c}
                        for p, s, c in r["folders"]],
            "extensions": [{"ext": e, "size": s, "count": c}
                           for e, s, c in r["extensions"]],
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.statusBar().showMessage(self.t("msg_exported", path=path), 5000)
        except OSError as e:
            QMessageBox.critical(self, self.t("msg_error"), str(e))

    def _export_html(self):
        if not self._ensure_results(): return
        path, _ = QFileDialog.getSaveFileName(self, self.t("export_html"),
                                               "report.html", "HTML (*.html)")
        if not path: return
        r = self._last_result
        total = r["total"] or 1
        when = time.strftime("%Y-%m-%d %H:%M",
                              time.localtime(r.get("timestamp") or time.time()))

        def esc(s):
            return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                    .replace(">", "&gt;"))

        def rfile(p, s):
            return f"<tr><td>{esc(p)}</td><td class='n'>{human_size(s)}</td><td class='n'>{s/total*100:.2f}%</td></tr>"

        def rfolder(p, s, c):
            return f"<tr><td>{esc(p)}</td><td class='n'>{human_size(s)}</td><td class='n'>{s/total*100:.2f}%</td><td class='n'>{c:,}</td></tr>"

        def rext(e, s, c):
            lbl = self.t("no_ext") if e == "__no_ext__" else e
            return f"<tr><td>{esc(lbl)}</td><td class='n'>{human_size(s)}</td><td class='n'>{s/total*100:.2f}%</td><td class='n'>{c:,}</td></tr>"

        html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>{esc(self.t('app_title'))}</title><style>
body{{font-family:Segoe UI,Tahoma,sans-serif;background:#0b0b0b;color:#e6e6e6;margin:24px}}
h1{{color:#8ec7ff}}h2{{color:#ffb27a;border-bottom:1px solid #333;padding-bottom:6px}}
table{{border-collapse:collapse;width:100%;margin-bottom:24px}}
th,td{{border:1px solid #333;padding:6px 10px;text-align:left;font-size:10pt}}
th{{background:#1c1c1c;color:#cfcfcf}}
tr:nth-child(even) td{{background:#111}}
td.n{{text-align:right}}
.meta{{color:#999;margin-bottom:18px}}
.dev{{color:#8ec7ff;font-weight:bold}}
</style></head><body>
<h1>{esc(self.t('app_title'))}</h1>
<div class="meta"><b>{esc(self.t('path_label'))}</b> {esc(r.get('root',''))} |
<b>Date:</b> {when} | <b>Total:</b> {human_size(r['total'])} |
<b>Files:</b> {r.get('scanned', len(r['files'])):,} |
<span class="dev">Developer: Craftou سهيل</span></div>
<h2>{esc(self.t('header_folders'))}</h2>
<table><thead><tr><th>{esc(self.t('col_folder'))}</th><th>{esc(self.t('col_size'))}</th>
<th>{esc(self.t('col_percent'))}</th><th>{esc(self.t('col_count'))}</th></tr></thead><tbody>
{''.join(rfolder(p,s,c) for p,s,c in r['folders'][:100])}
</tbody></table>
<h2>{esc(self.t('header_files'))}</h2>
<table><thead><tr><th>{esc(self.t('col_name'))}</th><th>{esc(self.t('col_size'))}</th>
<th>{esc(self.t('col_percent'))}</th></tr></thead><tbody>
{''.join(rfile(row[0],row[1]) for row in r['files'][:200])}
</tbody></table>
<h2>{esc(self.t('header_types'))}</h2>
<table><thead><tr><th>{esc(self.t('col_ext'))}</th><th>{esc(self.t('col_size'))}</th>
<th>{esc(self.t('col_percent'))}</th><th>{esc(self.t('col_count'))}</th></tr></thead><tbody>
{''.join(rext(e,s,c) for e,s,c in r['extensions'][:100])}
</tbody></table>
</body></html>"""
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            self.statusBar().showMessage(self.t("msg_exported", path=path), 5000)
        except OSError as e:
            QMessageBox.critical(self, self.t("msg_error"), str(e))

    def _show_about(self):
        QMessageBox.information(self, self.t("about"), self.t("about_text"))

    def closeEvent(self, event):
        for w in (self.worker, self.tool_worker):
            if w is not None and w.isRunning():
                w.stop(); w.wait(3000)
        event.accept()


# ============================================================
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Disk Space Analyzer")
    icon = get_app_icon()
    app.setWindowIcon(icon)
    app.setFont(QFont("Segoe UI", 10))
    win = MainWindow()
    win.setWindowIcon(icon)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()