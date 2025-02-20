{
    'name': "HR Resignation Management",
    'version': '1.0',
    'description': """
       A product of Bac Ha Software provides solution to resignation process for employees
    """,
    'author': 'Bac Ha Software',
    'company': 'Bac Ha Software',
    'maintainer': 'Bac Ha Software',
    'website': "https://bachasoftware.com",
    'category': 'Human Resources',
    'depends': ['hr', 'hr_resignation'],
    'data': [
        'data/departure_code_add.xml',
        'data/resignation_mail_template_data.xml',
        'security/ir.model.access.csv',
        'views/departure_reason_extend.xml',
        'views/resignation_view.xml'

    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False
}