import ast, datetime, types, json
from pathlib import Path
APP=(Path(__file__).resolve().parents[1] / 'app.py').read_text(encoding='utf-8')
class State(dict):
 def __getattr__(self,k):
  try:return self[k]
  except KeyError:raise AttributeError(k)
 def __setattr__(self,k,v):self[k]=v

def getfn(name,ns):
 node=next(n for n in ast.parse(APP).body if isinstance(n,ast.FunctionDef) and n.name==name)
 node.decorator_list=[]
 exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'delivered/app.py','exec'),ns)
 return ns[name]

def sync_context():
 state=State(); required=['FLOAT_REPORT','FLOAT_PAINT_SUMMARY','SHOP_WISE_REPORT','TCF1_VGL','TCF2_VGL','HOURLY_PRODUCTION']
 dl=types.SimpleNamespace(download_from_onedrive=lambda u:b'unchanged content',parse_onedrive_workbook=lambda b:{k:object() for k in required})
 ns={'st':types.SimpleNamespace(session_state=state),'dl':dl,'datetime':datetime,'format_ist_now':lambda fmt:'2026-09-23 10:00'}
 return state,dl,getfn('perform_onedrive_sync',ns)

def reset_sync():
 state,dl,sync=sync_context();assert sync('local.xlsx')[0]
 for key in list(state):
  if key.startswith(('buffer_','upload_time_')):del state[key]
 result=sync('local.xlsx');count=sum(k.startswith('buffer_') for k in state)
 assert count==6,f'Sync returned {result}; restored {count}/6 buffers after reset'
 return 'Restores all report buffers after reset'
def recover_sync():
 state,dl,sync=sync_context();sync('local.xlsx')
 dl.download_from_onedrive=lambda u:(_ for _ in ()).throw(ValueError('Temporary outage'))
 assert not sync('local.xlsx')[0]
 dl.download_from_onedrive=lambda u:b'unchanged content';assert sync('local.xlsx')[0]
 assert not state.get('_sync_error'),f'Recovery left old error visible: {state.get("_sync_error")}'
 return 'Successful unchanged sync clears previous error'
def partial_sync():
 state,dl,sync=sync_context();sync('local.xlsx');old=state['buffer_FLOAT_REPORT']
 dl.download_from_onedrive=lambda u:b'new content';dl.parse_onedrive_workbook=lambda b:{'FLOAT_REPORT':object()}
 assert not sync('local.xlsx')[0];assert state['buffer_FLOAT_REPORT'] is old
 return 'Incomplete workbook leaves previous buffers intact'
def paused_dispatch():
 state=State(run_report=False,telegram_auto_send_15m=True,telegram_token='TEST',telegram_chat_id='TEST',_report_snapshot={'sentinel':1})
 sends=[]
 dl=types.SimpleNamespace(load_metadata=lambda k,d='':d,dispatch_scheduled_reports=lambda *a:sends.append(a))
 ns={'st':types.SimpleNamespace(session_state=state,warning=lambda *a:None),'dl':dl,'datetime':datetime,
 'get_ist_now':lambda:datetime.datetime(2026,9,23,10,15),'_build_telegram_reports':lambda:('one','two','three')}
 getfn('monitor_sources',ns)()
 assert not sends,f'Timer dispatched {len(sends)} cached report bundle while run_report=False'
 return 'Paused calculations prevent automatic dispatch'

import unittest
class SyncRegressionTests(unittest.TestCase):
    def test_reset_restores_identical_workbook(self): reset_sync()
    def test_recovered_sync_clears_error(self): recover_sync()
    def test_partial_workbook_preserves_buffers(self): partial_sync()
    def test_paused_report_cannot_auto_send(self): paused_dispatch()
    def test_restored_buffers_trigger_screen_refresh(self):
        state=State(_sync_revision=1, _last_sync_digest='unchanged')
        refreshes=[]
        def synchronize(url):
            state['_sync_revision'] += 1
            return True, 'Restored'
        ns={'st':types.SimpleNamespace(session_state=state, warning=lambda *args:None, rerun=lambda:refreshes.append(True)),
            'dl':types.SimpleNamespace(load_metadata=lambda key,default='': 'source.xlsx' if key=='onedrive_url' else default),
            'datetime':datetime, 'perform_onedrive_sync':synchronize}
        getfn('monitor_sources',ns)()
        self.assertEqual(refreshes,[True])

if __name__ == '__main__': unittest.main()
