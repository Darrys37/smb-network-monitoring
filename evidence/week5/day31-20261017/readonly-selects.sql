-- Run manually using local privileged MySQL access on MON01. Read-only; no credentials.
SELECT h.host,hm.macro,hm.value FROM hostmacro hm JOIN hosts h ON h.hostid=hm.hostid WHERE h.host IN ('Linux by Zabbix agent','Zabbix server','SRV01','CLI01') AND hm.macro IN ('{$AGENT.TIMEOUT}','{$CPU.UTIL.CRIT}','{$LOAD_AVG_PER_CPU.MAX.WARN}') ORDER BY h.host,hm.macro;
SELECT h.host,t.host FROM hosts_templates ht JOIN hosts h ON h.hostid=ht.hostid JOIN hosts t ON t.hostid=ht.templateid WHERE h.hostid IN (10084,10683,10684) ORDER BY h.hostid,t.host;
SELECT 'GLOBAL_OVERRIDES',COUNT(*) FROM globalmacro WHERE macro IN ('{$AGENT.TIMEOUT}','{$CPU.UTIL.CRIT}','{$LOAD_AVG_PER_CPU.MAX.WARN}');
SELECT f.triggerid,f.functionid,f.itemid,f.name,f.parameter FROM functions f JOIN items i ON i.itemid=f.itemid WHERE (i.hostid=10683 AND f.triggerid IN (25249,25250,25260,25334)) OR (i.hostid=10684 AND f.triggerid=25335) ORDER BY f.triggerid,f.functionid;
