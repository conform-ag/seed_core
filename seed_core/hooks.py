app_name = "seed_core"
app_title = "Seed Core"
app_publisher = "aremtech"
app_description = "Vertical Domain App - Seed Management ERP"
app_email = "hello@aremtech.io"
app_license = "mit"

# Apps
# ------------------

required_apps = ["erpnext"]

# Fixtures - exported automatically on bench export-fixtures
fixtures = [
	{"dt": "Role", "filters": [["role_name", "in", ["Seed Geneticist", "Lab Technician", "Seed Processing Officer", "Sales Planner"]]]},
	{"dt": "Workspace", "filters": [["module", "=", "Seed Core"]]}
]

# Custom Fields
custom_fields = {
	"Batch": [
		{
			"fieldname": "seed_quality_section",
			"fieldtype": "Section Break",
			"label": "Seed Quality",
			"insert_after": "manufacturing_date"
		},
		{
			"fieldname": "germination_percent",
			"fieldtype": "Float",
			"label": "Germination %",
			"precision": "2",
			"insert_after": "seed_quality_section",
			"in_list_view": 1
		},
		{
			"fieldname": "purity_percent",
			"fieldtype": "Float",
			"label": "Purity %",
			"precision": "2",
			"insert_after": "germination_percent"
		},
		{
			"fieldname": "moisture_percent",
			"fieldtype": "Float",
			"label": "Moisture %",
			"insert_after": "purity_percent"
		},
		{
			"fieldname": "seed_vigor",
			"fieldtype": "Select",
			"label": "Vigor",
			"options": "\nHigh\nMedium\nLow",
			"insert_after": "moisture_percent"
		},
		{
			"fieldname": "quality_column_break",
			"fieldtype": "Column Break",
			"insert_after": "seed_vigor"
		},
		{
			"fieldname": "lab_test_date",
			"fieldtype": "Date",
			"label": "Lab Test Date",
			"insert_after": "quality_column_break"
		},
		{
			"fieldname": "next_retest_date",
			"fieldtype": "Date",
			"label": "Next Retest Date",
			"read_only": 1,
			"insert_after": "lab_test_date",
			"description": "Calculated based on Seed Core Settings"
		},
		{
			"fieldname": "seed_treatments_section",
			"fieldtype": "Section Break",
			"label": "Seed Treatments",
			"insert_after": "next_retest_date"
		},
		{
			"fieldname": "is_pelleted",
			"fieldtype": "Check",
			"label": "Is Pelleted",
			"insert_after": "seed_treatments_section"
		},
		{
			"fieldname": "is_primed",
			"fieldtype": "Check",
			"label": "Is Primed",
			"insert_after": "is_pelleted"
		},
		{
			"fieldname": "is_coated",
			"fieldtype": "Check",
			"label": "Is Coated",
			"insert_after": "is_primed"
		},
		{
			"fieldname": "is_chemically_treated",
			"fieldtype": "Check",
			"label": "Is Chemically Treated",
			"insert_after": "is_coated"
		},
		{
			"fieldname": "treatments_column_break",
			"fieldtype": "Column Break",
			"insert_after": "is_chemically_treated"
		},
		{
			"fieldname": "treatment_name",
			"fieldtype": "Data",
			"label": "Treatment Name",
			"insert_after": "treatments_column_break",
			"description": "e.g., Thiram + Apron"
		},
		{
			"fieldname": "seed_certifications_section",
			"fieldtype": "Section Break",
			"label": "Seed Certifications",
			"insert_after": "treatment_name"
		},
		{
			"fieldname": "is_organic",
			"fieldtype": "Check",
			"label": "Is Organic",
			"insert_after": "seed_certifications_section"
		},
		{
			"fieldname": "is_gspp",
			"fieldtype": "Check",
			"label": "Is GSPP",
			"insert_after": "is_organic",
			"description": "Good Seed and Plant Practices certified"
		}
    ],
    "Customer": [
        {
            "fieldname": "sales_agent_code",
            "fieldtype": "Data",
            "label": "Sales Agent Code",
            "insert_after": "customer_name"
        },
        {
            "fieldname": "farming_type",
            "fieldtype": "Select",
            "label": "Farming Type",
            "options": "\nMonocrop\nMulticrop",
            "insert_after": "sales_agent_code"
        },
        {
            "fieldname": "influence_level",
            "fieldtype": "Select",
            "label": "Influence Level",
            "options": "\nHigh\nMedium\nLow",
            "insert_after": "farming_type"
        },
        {
            "fieldname": "customer_grade",
            "fieldtype": "Select",
            "label": "Customer Grade",
            "options": "\nClass A\nClass B\nClass C",
            "insert_after": "influence_level"
        },
        {
            "fieldname": "is_cooperative",
            "fieldtype": "Check",
            "label": "Is Cooperative",
            "insert_after": "customer_grade"
        }
    ],
    "Sales Invoice": [
        {
            "fieldname": "cooperative_member",
            "fieldtype": "Link",
            "label": "Cooperative Member",
            "options": "Cooperative Member",
            "insert_after": "customer",
            "depends_on": "eval:frappe.db.get_value('Customer', doc.customer, 'is_cooperative') == 1" 
             # Note: depends_on in Custom Field might not work perfectly with DB calls in JS eval without async, 
             # better to handle visibility via JS or simple depends_on if field mapped. 
             # We will handle filtering in JS.
        }
    ],
    "Sales Order": [
        {
            "fieldname": "cooperative_member",
            "fieldtype": "Link",
            "label": "Cooperative Member",
            "options": "Cooperative Member",
            "insert_after": "customer"
        }
    ],
    "Delivery Note": [
        {
            "fieldname": "cooperative_member",
            "fieldtype": "Link",
            "label": "Cooperative Member",
            "options": "Cooperative Member",
            "insert_after": "customer"
        }
    ]
}


# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "seed_core",
# 		"logo": "/assets/seed_core/logo.png",
# 		"title": "Seed Core",
# 		"route": "/seed_core",
# 		"has_permission": "seed_core.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/seed_core/css/seed_core.css"
# app_include_js = "/assets/seed_core/js/seed_core.js"

# include js, css files in header of web template
# web_include_css = "/assets/seed_core/css/seed_core.css"
# web_include_js = "/assets/seed_core/js/seed_core.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "seed_core/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# include js in doctype views
doctype_js = {
    "Sales Invoice": "public/js/cooperative_transaction.js",
    "Sales Order": "public/js/cooperative_transaction.js",
    "Delivery Note": "public/js/cooperative_transaction.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "seed_core/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "seed_core.utils.jinja_methods",
# 	"filters": "seed_core.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "seed_core.install.before_install"
# after_install = "seed_core.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "seed_core.uninstall.before_uninstall"
# after_uninstall = "seed_core.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "seed_core.utils.before_app_install"
# after_app_install = "seed_core.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "seed_core.utils.before_app_uninstall"
# after_app_uninstall = "seed_core.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "seed_core.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Stock Entry": {
		"validate": "seed_core.seed_core.stock_mixing_validation.validate_stock_mixing"
	},
	"Stock Reconciliation": {
		"validate": "seed_core.seed_core.stock_mixing_validation.validate_stock_mixing"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"seed_core.tasks.all"
# 	],
# 	"daily": [
# 		"seed_core.tasks.daily"
# 	],
# 	"hourly": [
# 		"seed_core.tasks.hourly"
# 	],
# 	"weekly": [
# 		"seed_core.tasks.weekly"
# 	],
# 	"monthly": [
# 		"seed_core.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "seed_core.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "seed_core.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "seed_core.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "seed_core.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["seed_core.utils.before_request"]
# after_request = ["seed_core.utils.after_request"]

# Job Events
# ----------
# before_job = ["seed_core.utils.before_job"]
# after_job = ["seed_core.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"seed_core.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

