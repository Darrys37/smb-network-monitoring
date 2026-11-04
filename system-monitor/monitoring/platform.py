"""Conservative lab gate: kernel/package instability must not become a passed demo."""
HOSTS={'mon01','srv01','cli01'}
def ready(report):
 if not isinstance(report,dict) or report.get('status')!='ok' or report.get('schema_version')!=2:return False
 nodes=report.get('nodes',{})
 if not isinstance(nodes,dict) or set(nodes)!=HOSTS:return False
 for node in nodes.values():
  if not isinstance(node,dict):return False
  if type(node.get('stall_count')) is not int or node['stall_count']!=0:return False
  if node.get('recent_stall') is not False or node.get('package_jobs_active') is not False or node.get('dpkg_lock_held') is not False or node.get('package_audit_clean') is not True:return False
  if not isinstance(node.get('boot_id'),str) or not node['boot_id']:return False
  digest=node.get('package_status_sha256')
  if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):return False
 return True
def unchanged(before,after):
 return ready(before) and ready(after) and all(before['nodes'][h]['boot_id']==after['nodes'][h]['boot_id'] and before['nodes'][h]['package_status_sha256']==after['nodes'][h]['package_status_sha256'] for h in HOSTS)
