"""Small regression suite; run: python -m unittest discover -s tests -v."""
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest

import openpyxl
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import allocation_engine as engine
import dashboard_ui as ui
import data_loader as loader


class DashboardRegressionTests(unittest.TestCase):
    def test_fifo_balances_and_input_preservation(self):
        bom = pd.DataFrame([{'Short Vehicle Code':'123456789','Engine':'E','Cockpit':'C','Front Wiring':'W'}])
        queue = pd.DataFrame([{'VEHICLE CODE':'123456789X','BIW NUMBER':str(i)} for i in range(3)])
        engines, cockpits, wiring = {'E':2}, {'C':3}, {'W':3}
        rows, stocks = engine.run_allocation(queue,bom,engines,cockpits,wiring)
        self.assertEqual([row['STATUS'] for row in rows], ['✅ Ready for TCF','✅ Ready for TCF','🚫 Blocked'])
        self.assertEqual(stocks, {'engine':{'E':0},'cockpit':{'C':1},'wiring':{'W':1}})
        self.assertEqual(engines, {'E':2})
        self.assertEqual(cockpits, {'C':3})

    def test_bom_lookup_retains_first_duplicate(self):
        bom = pd.DataFrame([{'Short Vehicle Code':'123456789','Engine':'E','Cockpit':'C','Front Wiring':'W'},
                            {'Short Vehicle Code':'123456789','Engine':'OTHER','Cockpit':'C','Front Wiring':'W'}])
        queue = pd.DataFrame([{'VEHICLE CODE':'123456789X'}])
        rows, _ = engine.run_allocation(queue,bom,{'E':1},{'C':1},{'W':1})
        self.assertEqual(rows[0]['Engine_Part'],'E')
        self.assertEqual(rows[0]['STATUS'],'✅ Ready for TCF')

    def test_buffer_identity_ignores_cursor_but_detects_content(self):
        buffer = io.BytesIO(b'first')
        identity = ui.fingerprint(buffer)
        buffer.seek(3)
        self.assertEqual(identity, ui.fingerprint(buffer))
        buffer.seek(0); buffer.write(b'other')
        self.assertNotEqual(identity, ui.fingerprint(buffer))

    def test_file_identity_detects_same_path_update(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'source.xlsx';path.write_bytes(b'a')
            initial=ui.fingerprint(str(path))
            path.write_bytes(b'changed')
            self.assertNotEqual(initial,ui.fingerprint(str(path)))

    def test_parser_cache_is_separate_per_function(self):
        @loader.cached_file_loader
        def first(source): return 'first parser'
        @loader.cached_file_loader
        def second(source): return 'second parser'
        source=loader.WorkbookSheet(pd.DataFrame({'x':[1]}),'same.xlsx','same-content')
        self.assertEqual(first(source),'first parser')
        self.assertEqual(second(source),'second parser')

    def test_direct_sheet_preserves_normal_and_headerless_read(self):
        frame=pd.DataFrame({'VC':['123456789'],'Quantity':[12]})
        original=io.BytesIO();frame.to_excel(original,index=False);original.seek(0)
        frame=pd.read_excel(original)  # The master workbook has already been read once.
        output=io.BytesIO();frame.to_excel(output,index=False);output.seek(0)
        direct=loader.WorkbookSheet(frame,'sheet.xlsx','id')
        pd.testing.assert_frame_equal(loader._read_excel(direct),pd.read_excel(output),check_dtype=False)
        output.seek(0)
        pd.testing.assert_frame_equal(loader._read_excel(direct,header=None),pd.read_excel(output,header=None),check_dtype=False)

    def test_empty_exports_are_valid_workbooks(self):
        data=ui.table_workbook({'Cockpit WH':pd.DataFrame(),'Wiring':pd.DataFrame()})
        workbook=openpyxl.load_workbook(io.BytesIO(data))
        self.assertEqual(workbook.sheetnames,['Cockpit WH','Wiring'])


if __name__ == '__main__':
    unittest.main()
