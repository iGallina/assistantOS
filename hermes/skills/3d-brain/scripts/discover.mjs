import {promises as fs} from 'node:fs';
import path from 'node:path';
const at=process.argv.indexOf('--root');
const root=path.resolve(at>=0?process.argv[at+1]:process.cwd());
const candidates=[];
async function add(label,p,type='markdown'){try{const stat=await fs.stat(p);candidates.push({label,path:p,type,isDirectory:stat.isDirectory()});}catch{}}
// root = the Hermes profile folder ($HERMES_HOME). Owner data lives in local/; Hermes keeps its own memory and skills.
for(const [label,p] of [['Contexto do negócio','local/context'],['Entrevistas','local/brainstorms'],['Reuniões','local/meetings'],['Agentes de contato','local/agentes'],['Auditorias','local/audits'],['Memória do assistente','memories'],['Skills','skills']]) await add(label,path.join(root,p));
console.log(JSON.stringify({root,candidates,note:'Candidate paths only. Ask the user for their name and categories; confirm which paths to include before reading external memory. Add custom category paths as needed.'},null,2));
