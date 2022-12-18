{
    'name' : 'Inventory and Stock Valuation Report App',
    'author': "Edge Technologies",
    'version' : '15.0.1.0',
    'live_test_url':'https://www.youtube.com/watch?v=NK0BhuKdvAI',
    "images":["static/description/main_screenshot.png"],
    'summary' : 'Inventory Valuation Reports Inventory Stock Valuation Report for warehouse Valuation report for warehouse stock valuation summary reports print stock valuation report print inventory valuation report stock summary report inventory valuation summary report',
    'description' : """
        Inventory and Stock Valuation Report App.
    """,
    'depends' : ['base','sale_management','purchase','stock'],
    "license" : "OPL-1",
    'data': [
            'security/ir.model.access.csv',
            'report/stock_valution_report.xml',
            'report/stock_valution_report_template.xml',
            'wizard/stock_valution_report_view.xml',
            ],
    'qweb' : [],
    'demo' : [],
    'installable' : True,
    'auto_install' : False,
    'price': 18,
    'currency': "EUR",
    'category' : 'Warehouse',
}
