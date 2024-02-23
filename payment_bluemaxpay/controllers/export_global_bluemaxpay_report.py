# -*- coding: utf-8 -*-

import io
import json
from odoo import fields, http
from odoo.http import request, content_disposition
from odoo.tools import osutil
from odoo.tools.misc import xlsxwriter
from datetime import datetime

class BluemaxpayXlsxExport(http.Controller):

    def isfloat(self, num):
        try:
            if ',' in num:
                num = num.replace(',', '')
            float(num)
            return True
        except ValueError:
            return False

    @http.route(
        [
            "/bmpay/report/export_xlsx"
        ],
        type="http",
        auth="user",
    )
    def bluemaxpay_report_export(self, data, startDate, endDate, **kw):
        jdata = json.loads(data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Bluemax Pay Global Report')
        worksheet.set_column('G:H', 14)
        worksheet.set_column('K:L', 17)
        worksheet.set_column('M:N', 11)
        right_align = workbook.add_format({'align': 'right'})
        left_align = workbook.add_format({'align': 'left'})
        bold_center_align = workbook.add_format(
            {'align': 'center', 'bold': True})
        row = 0
        for tr in jdata:
            if tr[4] == 'Date' or startDate <= tr[4][:-9] <= endDate:
                col = 0
                first_column_skipped = False
                duplicate_encountered = False
                for th in tr:
                    if not row:
                        if th and len(th):
                            worksheet.merge_range(
                                row, col, row, col + 1, th, bold_center_align)
                            col += 2
                    else:
                        if not first_column_skipped:
                            first_column_skipped = True
                            continue
                        if th and self.isfloat(th):
                            if ',' in th:
                                th = th.replace(',', '')
                            if not float(th):
                                worksheet.merge_range(
                                    row, col, row, col + 1, "", left_align)
                                col += 2
                            else:
                                worksheet.merge_range(
                                    row, col, row, col + 1, int(float(th)), left_align)
                                col += 2
                        else:
                            worksheet.merge_range(
                                row, col, row, col + 1, th, left_align)
                            col += 2
                row += 1

        workbook.close()
        xlsx_data = output.getvalue()
        filename = osutil.clean_filename("Bluemax Pay Global Report")
        response = request.make_response(xlsx_data,
                                         headers=[('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                                                  ('Content-Disposition', content_disposition(filename + '.xlsx'))],
                                         )

        return response
