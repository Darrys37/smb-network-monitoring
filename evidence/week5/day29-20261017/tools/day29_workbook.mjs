import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';
const out=path.resolve('outputs/week5-day29-20261017');
const input=JSON.parse(await fs.readFile(path.join(out,'workbook-input.json'),'utf8'));
const wb=Workbook.create();
const sum=wb.worksheets.add('Tong_hop'), data=wb.worksheets.add('Du_lieu');
const keys=['run_id','scenario','problem_event_id','recovery_event_id','incident_id','fault_before_epoch','fault_after_epoch','problem_epoch','rollback_before_epoch','rollback_after_epoch','recovery_epoch','cli_elapsed_seconds','target_status','valid_fault','detected','engine_exit_code','review_issue_count','dt_lower_seconds','dt_upper_seconds','rr_lower_seconds','rr_upper_seconds','target_success'];
const headers=['Run ID','Kịch bản','Problem ID','Recovery ID','Incident ID','Fault trước (epoch)','Fault sau (epoch)','Problem (epoch)','Rollback trước','Rollback sau','Recovery (epoch)','CLI (giây)','Luật mục tiêu','Fault hợp lệ','Phát hiện','CLI exit','Lỗi kiểm tra','DT dưới (giây)','DT trên (giây)','RR dưới (giây)','RR trên (giây)','Thành công'];
data.getRange('A1:V19').values=[headers,...input.rows.map(r=>keys.map(k=>r[k]))];
for(let r=2;r<=19;r++){
 data.getRange(`R${r}:V${r}`).formulas=[[`=H${r}-G${r}`,`=H${r}-F${r}`,`=K${r}-J${r}`,`=K${r}-I${r}`,`=IF(AND(N${r}=1,M${r}="matched",Q${r}=0,P${r}=0),1,0)`]];
}
data.getRange('A22:V22').merge(); data.getRange('A22').values=[['Nguồn: evidence/week4/official-runs/<Run ID>/{fault.log, rollback.log, run.json, incident.json, problem-after-recovery.json, recovery.json}']];
data.getRange('A24:V24').merge(); data.getRange('A24').values=[['Epoch UTC; 1 giây độ phân giải. 18 dòng đã kiểm tra, không thêm/xóa dòng trong bảng nghiệm thu. CSV chứa thêm đường dẫn ảnh và cận DT ±1 giây.']];
sum.getRange('A1:J1').merge(); sum.getRange('A1').values=[['TUẦN 5 · NGÀY 29 | KIỂM TRA DỮ LIỆU']];
const notes={3:'17/10/2026 · 19 lượt theo dõi · 18 fault hợp lệ · 1 lượt hủy trước fault',4:'Đã đối chiếu 631 checksum và 18 liên kết event–incident–recovery–ảnh.',15:'Tỷ lệ = tử số / fault hợp lệ. Không có mẫu âm để tính accuracy tổng quát/FPR.',17:'Thời gian (giây) · DT/RR dùng cận dưới; cận trên có tại Du_lieu và CSV.',27:'n=3 mỗi kịch bản; min/median/max chỉ mô tả mẫu thử, chưa chứng minh tổng quát.',29:'DT = problem − fault sau. RR = recovery − rollback sau; không phải downtime.',30:'CLI gồm API, thu thập, luật và lưu DB. Timestamp độ phân giải 1 giây.',32:'R5-03 hủy trước gây lỗi: loại khỏi mẫu số; R5-03-retry1 được tính hợp lệ.',33:'Giữ insufficient_evidence ở luật phụ; không thay bằng not_matched/true negative.',34:'Baseline 30 phút 06 giây; ảnh event chụp hồi cứu sau phục hồi.',36:'Công thức thống kê dùng nhóm 3 Run ID cố định theo kịch bản trong bảng đã nghiệm thu.'};
for(const [r,t] of Object.entries(notes)){sum.getRange(`A${r}:J${r}`).merge();sum.getRange(`A${r}`).values=[[t]];}
sum.getRange('A6:I6').values=[['Kịch bản','Fault hợp lệ','Phát hiện','Mục tiêu khớp','CLI lỗi','Thiếu bằng chứng','Không phát hiện','Tỷ lệ phát hiện','Tỷ lệ mục tiêu']];
for(let i=0;i<6;i++){
 const r=i+7;sum.getRange(`A${r}`).values=[[`R${i+1}`]];
 sum.getRange(`B${r}:I${r}`).formulas=[[
 `=SUMIF(Du_lieu!$B$2:$B$19,A${r},Du_lieu!$N$2:$N$19)`,
 `=SUMIF(Du_lieu!$B$2:$B$19,A${r},Du_lieu!$O$2:$O$19)`,
 `=SUMIF(Du_lieu!$B$2:$B$19,A${r},Du_lieu!$V$2:$V$19)`,
 `=COUNTIFS(Du_lieu!$B$2:$B$19,A${r},Du_lieu!$P$2:$P$19,"<>0")`,
 `=COUNTIFS(Du_lieu!$B$2:$B$19,A${r},Du_lieu!$M$2:$M$19,"insufficient_evidence")`,
 `=B${r}-C${r}`,`=IF(B${r}=0,"n.a.",C${r}/B${r})`,`=IF(B${r}=0,"n.a.",D${r}/B${r})`]];
}
sum.getRange('A13').values=[['Tổng']];for(const c of ['B','C','D','E','F','G'])sum.getRange(`${c}13`).formulas=[[`=SUM(${c}7:${c}12)`]];
sum.getRange('H13:I13').formulas=[['=C13/B13','=D13/B13']];
sum.getRange('A19:J19').values=[['Kịch bản','DT min','DT median','DT max','CLI min','CLI median','CLI max','RR min','RR median','RR max']];
for(let i=0;i<6;i++){
 const r=20+i,first=2+i*3,last=first+2;sum.getRange(`A${r}`).values=[[`R${i+1}`]];
 const formulas=[];for(const c of ['R','L','T'])for(const f of ['MIN','MEDIAN','MAX'])formulas.push(`=${f}(Du_lieu!${c}${first}:${c}${last})`);
 sum.getRange(`B${r}:J${r}`).formulas=[formulas];
}
for(const [s,area] of [[sum,'A1:J36'],[data,'A1:V24']]){
 s.showGridLines=false;s.getRange(area).format.font={name:'Arial',size:10,color:'#243746'};s.getRange(area).format.rowHeight=23;s.getRange(area).format.columnWidth=14;
 s.freezePanes.freezeRows(s===sum?6:1);s.freezePanes.freezeColumns(s===sum?1:2);
}
sum.getRange('A1:J1').format.font={size:17,bold:true,color:'#123C59'};sum.getRange('A1:J1').format.rowHeight=36;
for(const range of ['A6:I6','A19:J19']){sum.getRange(range).format.fill='#123C59';sum.getRange(range).format.font={bold:true,color:'#FFFFFF'};sum.getRange(range).format.wrapText=true;sum.getRange(range).format.rowHeight=45;}
sum.getRange('A13:I13').format.fill='#DCEDE8';sum.getRange('A13:I13').format.font={bold:true};
sum.getRange('H7:I13').setNumberFormat('0.0%');sum.getRange('B20:J25').setNumberFormat('0.000');
for(const r of Object.keys(notes)){sum.getRange(`A${r}:J${r}`).format.font={size:10,color:'#4B5965'};}
data.getRange('A1:V1').format.fill='#123C59';data.getRange('A1:V1').format.font={bold:true,color:'#FFFFFF'};data.getRange('A1:V1').format.wrapText=true;data.getRange('A1:V1').format.rowHeight=44;
data.getRange('A1:A19').format.columnWidth=21;data.getRange('M1:M19').format.columnWidth=24;data.getRange('F2:K19').setNumberFormat('0');data.getRange('L2:L19').setNumberFormat('0.000');data.getRange('R2:U19').setNumberFormat('0');data.getRange('R2:V19').format.fill='#EDF4FA';
wb.recalculate();
const near=(a,b)=>assert.ok(typeof a==='number' && Math.abs(a-b)<1e-8,`${a} != ${b}`);
for(let i=0;i<6;i++){
 const expected=input.summary[i];const actual=sum.getRange(`B${20+i}:J${20+i}`).values[0];
 const fields=['dt_lower_seconds','cli_elapsed_seconds','rr_lower_seconds'];let j=0;
 for(const field of fields)for(const stat of ['min','median','max'])near(actual[j++],expected[field+'_'+stat]);
 assert.deepEqual(sum.getRange(`B${7+i}:I${7+i}`).values[0],[3,3,3,0,0,0,1,1]);
}
data.getRange('M2').values=[['not_matched']];wb.recalculate();near(sum.getRange('D13').values[0][0],17);near(sum.getRange('I7').values[0][0],2/3);
data.getRange('M2').values=[['matched']];wb.recalculate();near(sum.getRange('D13').values[0][0],18);
const inspect=await wb.inspect({kind:'region',sheetId:'Tong_hop',range:'A6:I13',maxChars:4500,tableMaxRows:8,tableMaxCols:9});
await fs.writeFile(path.join(out,'workbook-inspection.ndjson'),inspect.ndjson);
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:100},maxChars:3000});
await fs.writeFile(path.join(out,'workbook-error-scan.ndjson'),errors.ndjson);
for(const [sheetName,range,file] of [['Tong_hop','A1:J36','summary-preview.png'],['Du_lieu','A1:H8','data-preview.png'],['Du_lieu','L1:V8','formulas-preview.png']]){
 const blob=await wb.render({sheetName,range,scale:1.4,format:'png'});await fs.writeFile(path.join(out,file),new Uint8Array(await blob.arrayBuffer()));
}
const file=await SpreadsheetFile.exportXlsx(wb);await file.save(path.join(out,'NGAY29_KIEM_TRA_DU_LIEU.xlsx'));
await fs.writeFile(path.join(out,'workbook-validation.json'),JSON.stringify({result:'PASS',statistics_numeric_comparisons:54,counts_and_rates_verified:48,dependency_mutation_and_restore:'PASS; temporary target status changes total 18 to 17 and R1 rate to 2/3, restored 18',native_excel_session_used:false},null,2));
console.log('Workbook exported; 54 statistics, 48 counts/rates and dependency mutation verified.');
