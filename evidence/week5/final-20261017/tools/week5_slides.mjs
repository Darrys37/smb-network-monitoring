import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
const workspaceDir=process.cwd();
const SKILL_DIR='C:/Users/Darrys/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations';
const RUNTIME_PYTHON='C:/Users/Darrys/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
const {finalizePresentation,resolvePresentationFont,applyPresentationChartFont}=await import(pathToFileURL(path.join(SKILL_DIR,'container_tools/artifact_tool_utils.mjs')).href);
const font=resolvePresentationFont({fontFamily:'Arial'});
const build=path.join(workspaceDir,'.week5-slides-build');const output=path.join(workspaceDir,'outputs/week5-final-20261017');
await fs.mkdir(build,{recursive:true});await fs.mkdir(output,{recursive:true});
const p=Presentation.create({slideSize:{width:1280,height:720}});
function text(slide,value,x,y,w,h,size=30,color='#173B52',bold=false){
 const shape=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 shape.text=value;shape.text.style={typeface:font,fontSize:size,color,bold};return shape;
}
function page(title,source){const s=p.slides.add();s.background.fill='#FAFCFD';text(s,title,65,42,1150,100,44,'#123C59',true);s.speakerNotes.text='Nguồn trong project C:/Users/Darrys/do-an/: '+source;return s;}
function paragraphs(s,items){items.forEach((v,i)=>text(s,v,76,180+i*105,1120,90,31,'#263D4D'));}
let s=page('Giám sát và hỗ trợ chẩn đoán\nsự cố mạng','docs/CHUONG_2_KIEN_TRUC_VA_TRIEN_KHAI.md');
text(s,'Zabbix 7.0 LTS · Python CLI · SQLite',70,305,1100,70,36,'#267B69');
text(s,'Lab ba máy ảo và 18 lượt thử có truy vết',70,410,1100,80,31);
text(s,'Báo cáo kỹ thuật · tháng 10/2026',70,585,1100,50,24,'#526775');
s=page('Bài toán và phạm vi','README.md; docs/CHUONG_2_KIEN_TRUC_VA_TRIEN_KHAI.md, mục2.1');
paragraphs(s,['Zabbix phát hiện triệu chứng qua metric và trigger.','Module thu bằng chứng để giải thích giả thuyết nguyên nhân.','Người vận hành chọn event và quyết định xử lý.','Sản phẩm dùng sáu luật; chưa tự khắc phục sự cố.']);
s=page('Mô hình lab','docs/CHUONG_2_KIEN_TRUC_VA_TRIEN_KHAI.md, mục2.2; evidence/week5/day31-20261017/virtualbox-runtime.json');
paragraphs(s,['MON01 .10: Zabbix, MySQL, frontend và Python CLI.','SRV01 .20: Nginx, Agent 2, đích thử HTTP và CPU.','CLI01 .30: Agent 2, observer DNS và host đối chứng.','Cùng Host-only /24; NAT riêng, không có gateway lab chung.']);
s=page('Luồng chẩn đoán và hồ sơ','diagnosis-engine/app.py; repository.py; recovery.py; report.py');
paragraphs(s,['Xác minh problem còn mở, đúng event và host.','Thu ping, TCP, metric và probe từ đúng observer.','Đánh giá luật, kiểm tra lại event rồi lưu transaction SQLite.','Xác minh recovery liên kết; giữ evidence gốc trong report.']);
s=page('Sáu luật có ba trạng thái','diagnosis-engine/roadmap_rules.py; docs/CHUONG_2_KIEN_TRUC_VA_TRIEN_KHAI.md, mục2.6');
text(s,'R1 kết nối host       R2 HTTP/service       R3 Agent',75,190,1130,80,32);
text(s,'R4 DNS                    R5 đường HTTP          R6 CPU',75,300,1130,80,32);
text(s,'matched · not_matched · insufficient_evidence',75,435,1130,70,34,'#267B69',true);
text(s,'R1/R2/R5 cùng dùng problem HTTP; evidence bổ sung giúp phân biệt.',75,550,1130,80,27,'#526775');
s=page('Thời gian phát hiện theo kịch bản','evidence/week5/day30-20261017/timing-summary.csv; plotted-points.csv. Values are lower-bound medians in seconds, not confidence intervals.');
let chart=s.charts.add('bar',{position:{left:85,top:160,width:1100,height:405},categories:['R1','R2','R3','R4','R5','R6'],series:[{name:'DT median cận dưới (giây)',values:[19,10,269,77,24,356],fill:'#267B69'}],hasLegend:false,barOptions:{direction:'column',grouping:'clustered'},dataLabels:{showValue:true,position:'outEnd'},yAxis:{minimumScale:0,numberFormatCode:'0',majorGridlines:{fill:'#DFE7EB',width:1}},xAxis:{numberFormatCode:'General'}});applyPresentationChartFont(chart,{fontFamily:font});
text(s,'n=3 mỗi loại · Cận dưới DT · Cận trên và từng lượt có trong CSV',80,610,1130,65,25,'#526775');
s=page('Luật mục tiêu khớp 18/18 fault hợp lệ','evidence/week5/day30-20261017/diagnosis-outcomes.csv; evidence/week5/day29-20261017/attempts.csv. Each scenario has3 valid faults; aborted R5-03 is excluded before injection.');
chart=s.charts.add('bar',{position:{left:85,top:155,width:1100,height:405},categories:['R1','R2','R3','R4','R5','R6'],series:[{name:'Khớp mục tiêu /3',values:[3,3,3,3,3,3],fill:'#267B69'}],hasLegend:false,barOptions:{direction:'column',grouping:'clustered'},dataLabels:{showValue:true,position:'outEnd'},yAxis:{minimumScale:0,maximumScale:4,numberFormatCode:'0'},xAxis:{numberFormatCode:'General'}});applyPresentationChartFont(chart,{fontFamily:font});
text(s,'Chưa có mẫu âm để tính accuracy tổng quát hoặc false-positive rate.',80,610,1130,70,26,'#526775');
s=page('Demo Nginx trong 10 phút','docs/KICH_BAN_DEMO_10_PHUT.md; docs/HUONG_DAN_CAI_DAT_VA_KHOI_PHUC.md');
paragraphs(s,['0–2 phút: topology, dashboard và trạng thái nền.','2–6 phút: timer rollback, dừng Nginx, problem và diagnosis.','6–8 phút: bật lại Nginx, recovery và incident closed.','8–10 phút: số liệu, giới hạn và hướng mở rộng.']);
s=page('Giới hạn của bộ thực nghiệm','docs/CHUONG_3_THUC_NGHIEM_VA_DANH_GIA.md; evidence/week4/official-runs/R5-02/incident.json');
paragraphs(s,['Ba lượt mỗi loại, cùng laptop và topology nhỏ.','Baseline 30 phút 06 giây; chưa đánh giá vận hành dài hạn.','24/108 đầu ra luật thiếu evidence; giữ nguyên trạng thái.','CLI elapsed gồm API, thu dữ liệu, luật và ghi SQLite.']);
s=page('Đóng góp và hướng mở rộng','docs/CAU_HOI_BAO_VE.md; docs/CHUONG_2_KIEN_TRUC_VA_TRIEN_KHAI.md');
paragraphs(s,['Hồ sơ truy vết event, evidence, luật và recovery đã xác minh.','Cơ chế từ chối dữ liệu thiếu, sai observer hoặc bundle trùng.','Bước tiếp theo: tập âm độc lập, nhiều host và topology.','Đo từng pha và response-time để kiểm chứng tác động ứng dụng.']);
for(const [i,slide] of p.slides.items.entries()){
 for(const c of slide.charts.items){c.xAxis={textStyle:{fontSize:24}};c.yAxis={min:0,...(i===6?{max:4,majorUnit:1}:{max:400,majorUnit:100}),textStyle:{fontSize:22}};c.dataLabels={textStyle:{fontSize:24}};applyPresentationChartFont(c,{fontFamily:font});}
}
for(let i=0;i<p.slides.items.length;i++){
 const blob=await p.export({slide:p.slides.items[i],format:'png',scale:1});await fs.writeFile(path.join(build,`slide-${i+1}.png`),new Uint8Array(await blob.arrayBuffer()));
}
const candidatePath=path.join(build,'candidate.pptx');await(await PresentationFile.exportPptx(p)).save(candidatePath);
const result=await finalizePresentation({workspaceDir,candidatePath,finalPath:path.join(output,'SLIDE_BAO_VE_TUAN5_FINAL.pptx'),pythonExecutable:RUNTIME_PYTHON,integrityValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],explicitTotalSlideCount:10,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[6,7],materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,receiptPath:path.join(build,'validation-final.json')});
console.log(JSON.stringify(result));
