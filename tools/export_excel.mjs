// Optional prepared Excel snapshot. Requires an available Artifact Tool runtime.
// Refresh source inputs first: python -m src.excel_inputs
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const data = JSON.parse(await fs.readFile(path.join(root,'reports/exports/excel_pack_inputs.json'),'utf8'));
const out = path.join(root,'outputs/restops');
await fs.mkdir(out,{recursive:true});
const wb = Workbook.create();
const currency = '#,##0;(#,##0);"—"';
const sheets = [];

function tableSheet(name,title,note,headers,rows,widths) {
  const sheet = wb.worksheets.add(name);
  sheet.showGridLines = false;
  sheet.tabColor = '#19191F';
  const last = String.fromCharCode(64+headers.length);
  sheet.getRange(`A1:${last}${rows.length+7}`).format.font = {name:'Arial',size:10,color:'#202027'};
  sheet.getRange('A2').values = [[title]];
  sheet.getRange('A2').format.font = {name:'Arial',size:14,bold:true,color:'#19191F'};
  sheet.getRange(`A2:${last}2`).format.rowHeight = 30;
  sheet.getRange(`A3:${last}3`).format.borders = {bottom:{style:'thin',color:'#FF3B30'}};
  sheet.getRange('A4').values = [[note]];
  sheet.getRange('A4').format.font = {name:'Arial',size:10,italic:true,color:'#55555F'};
  sheet.getRange(`A6:${last}6`).values = [headers];
  sheet.getRange(`A7:${last}${rows.length+6}`).values = rows;
  sheet.getRange(`A6:${last}6`).format = {fill:'#19191F',font:{name:'Arial',size:10,color:'#FFFFFF',bold:true},wrapText:true,horizontalAlignment:'center',verticalAlignment:'center',rowHeight:42};
  sheet.getRange(`A7:${last}${rows.length+6}`).format.rowHeight = 25;
  widths.forEach((width,i)=>sheet.getRange(`${String.fromCharCode(65+i)}1:${String.fromCharCode(65+i)}${rows.length+7}`).format.columnWidth = width);
  sheet.freezePanes.freezeRows(6);
  const table = sheet.tables.add(`A6:${last}${rows.length+6}`,true,`${name.replaceAll(' ','')}Table`);
  table.style = 'TableStyleLight1';
  table.showFilterButton = true;
  sheets.push(sheet);
  return sheet;
}

const weekly = tableSheet('Weekly review','RESTOPS weekly performance',`Seven days ${data.window_start} to ${data.window_end}. AUD excluding GST. Synthetic operation.`,data.weekly_headers,data.weekly,[25,17,17,13,13,13,13,13,15]);
weekly.getRange('B7:C24').setNumberFormat(currency);
weekly.getRange('D7:G24').setNumberFormat('0.0%');
weekly.getRange('H7:H24').setNumberFormat('#,##0');
weekly.getRange('I7:I24').setNumberFormat('0.0%');
weekly.getRange('D7:D24').conditionalFormats.add('cellIs',{operator:'lessThan',formula:.10,format:{fill:'#FCE8E6',font:{color:'#9C201C'}}});
weekly.getRange('G7:G24').conditionalFormats.add('cellIs',{operator:'lessThan',formula:1,format:{fill:'#FFF1D6',font:{color:'#7E4D13'}}});

const labourRows = data.labour.map(row=>row.map((v,i)=>i===1?new Date(`${v}T00:00:00Z`):v));
const labour = tableSheet('Labour planning','RESTOPS four-week labour planning',`Daily totals from origin ${data.forecast_origin}. 6 orders/service hour, 80% utilisation, AUD 35/hour. Scheduled comparison is a historical template.`,data.labour_headers,labourRows,[15,16,25,18,18,18,22,22]);
labour.getRange(`B7:B${labourRows.length+6}`).setNumberFormat('dd-mmm-yy');
labour.getRange(`D7:F${labourRows.length+6}`).setNumberFormat('#,##0.0');
labour.getRange(`G7:H${labourRows.length+6}`).setNumberFormat(currency);

const scenarioRows = data.scenario.map(row=>[row[0].replaceAll('_',' '),...row.slice(1)]);
const scenario = tableSheet('Scenario comparison','RESTOPS scenario comparison',data.scenario_note,data.scenario_headers,scenarioRows,[30,24,24,24]);
scenario.getRange(`B7:D${scenarioRows.length+6}`).setNumberFormat(currency);
data.scenario.forEach((row,i)=>{
  if (row[0].endsWith('_pct') || row[0].endsWith('_rate')) scenario.getRange(`B${i+7}:D${i+7}`).setNumberFormat('0.0%');
  else if (['transactions','paid_hours','break_even_orders'].includes(row[0])) scenario.getRange(`B${i+7}:D${i+7}`).setNumberFormat('#,##0.0');
});

const notes = wb.worksheets.add('ReadMe');
notes.showGridLines=false;
notes.tabColor='#B0B0BB';
notes.getRange('A1:B20').format.font={name:'Arial',size:10,color:'#202027'};
notes.getRange('A2').values=[['RESTOPS export scope']];
notes.getRange('A2').format.font={name:'Arial',size:14,bold:true};
notes.getRange('A4:B13').values=[
  ['Company','Southern Table Hospitality (fictional). All outcomes are synthetic.'],
  ['Workbook mode','Prepared, computed snapshot. No editable Excel scenario engine or live app synchronisation.'],
  ['Weekly source','reports/exports/weekly_performance.csv. One restaurant per rolling seven-day window.'],
  ['Targets','Calendar-day share of monthly target. Holiday timing can affect week comparisons.'],
  ['Planning source','reports/exports/labour_plan.csv. This sheet aggregates restaurant/date hourly estimates.'],
  ['Staffing limitation','Hourly suggestions are decision support. Availability, awards, break timing and shift construction are absent.'],
  ['Scenario source','reports/exports/scenario_comparison.csv. Wollongong December 2025 baseline and labelled assumptions.'],
  ['Cost definitions','COGS includes sold ingredients and waste once. Contribution is before overhead; profit deducts overhead.'],
  ['Break-even','Chosen labour hours, overhead and campaign spend fixed within period; variable unit costs unchanged.'],
  ['Current selections','Use app CSV/JSON downloads for current filters and sliders. These workbook values do not refresh automatically.'],
];
notes.getRange('A4:A13').format.font={name:'Arial',size:10,bold:true};
notes.getRange('A1:A20').format.columnWidth=25;
notes.getRange('B1:B20').format.columnWidth=115;
notes.getRange('A4:B13').format.rowHeight=32;
sheets.push(notes);

wb.recalculate();
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!',options:{useRegex:true,maxResults:30},summary:'Snapshot error scan',maxChars:1500});
console.log(errors.ndjson);
for (const sheet of sheets){
  const preview=await wb.render({sheetName:sheet.name,range:sheet.name==='ReadMe'?'A1:B14':sheet.name==='Scenario comparison'?'A1:D20':sheet.name==='Weekly review'?'A1:I24':'A1:H18',scale:1,format:'png'});
  await fs.writeFile(path.join(out,`${sheet.name.toLowerCase().replaceAll(' ','_')}.png`),new Uint8Array(await preview.arrayBuffer()));
}
const xlsx=await SpreadsheetFile.exportXlsx(wb);
await xlsx.save(path.join(out,'weekly_management_pack.xlsx'));
await fs.copyFile(path.join(out,'weekly_management_pack.xlsx'),path.join(root,'reports/exports/weekly_management_pack.xlsx'));
console.log('Exported weekly performance, labour planning and scenario snapshot with explicit scope.');
