// actualGoals/actualAssists/actualCS updated to July 1 2026
// Source: ESPN fifa.world API (automated daily at 06:00 UTC via world-cup-scraper Lambda)

export const SCORERS = [
  { rank:1, name:'Kylian Mbappé',   flag:'🇫🇷', club:'Real Madrid',    age:27, predGoals:7, actualGoals:6, actualAssists:2, form:'WWW', rating:9.6, confidence:88, odds:'+200', tag:'hot',   analysis:'6 goals — brace vs Sweden (Jun 30). Beat Paraguay in Last 16. France in QF vs Brazil. Golden Boot race.' },
  { rank:2, name:'Harry Kane',       flag:'🏴󠁧󠁢󠁥󠁮󠁧󠁿', club:'Bayern Munich',  age:32, predGoals:6, actualGoals:2, actualAssists:1, form:'WDW', rating:9.0, confidence:65, odds:'+400', tag:'value', analysis:'2 goals — England beat Belgium in Last 16. QF vs Argentina. Needs a big performance to reach SF.' },
  { rank:3, name:'Erling Haaland',   flag:'🇳🇴', club:'Man City',       age:25, predGoals:6, actualGoals:5, actualAssists:0, form:'WWW', rating:9.3, confidence:70, odds:'+350', tag:'hot',   analysis:'5 goals — tournament top scorer with Mbappé/Messi. Norway eliminated by Germany in Last 16. Golden Boot contender.' },
  { rank:4, name:'Julián Álvarez',   flag:'🇦🇷', club:'Atlético Madrid', age:24, predGoals:5, actualGoals:2, actualAssists:1, form:'WWW', rating:8.8, confidence:55, odds:'+700', tag:'value', analysis:'2 goals alongside Messi. Argentina perfect group — Álvarez feeds off Messi service.' },
  { rank:5, name:'Lamine Yamal',     flag:'🇪🇸', club:'Barcelona',      age:18, predGoals:5, actualGoals:1, actualAssists:2, form:'DWW', rating:9.0, confidence:52, odds:'+800', tag:'tip',   analysis:'1 goal, 2 assists. Spain beat Australia in Last 16. Spain in QF vs Germany.' },
  { rank:6, name:'Vinicius Jr.',     flag:'🇧🇷', club:'Real Madrid',    age:24, predGoals:5, actualGoals:4, actualAssists:1, form:'DWW', rating:8.9, confidence:50, odds:'+900', tag:'tip',   analysis:'4 goals — Brazil\'s star player has been electric. Beat USA in Last 16. QF vs France.' },
  // Other tournament leaders not in original predictions
  { rank:2, name:'Lionel Messi',     flag:'🇦🇷', club:'Inter Miami',    age:38, predGoals:3, actualGoals:6, actualAssists:0, form:'WWW', rating:9.5, confidence:85, odds:'+280', tag:'hot',   analysis:'6 goals — JOINT GOLDEN BOOT with Mbappé. Argentina beat Switzerland in Last 16. QF vs England. One last dance.' },
  { rank:8, name:'Ousmane Dembélé',  flag:'🇫🇷', club:'PSG',            age:28, predGoals:3, actualGoals:4, actualAssists:1, form:'WWW', rating:8.6, confidence:60, odds:'+500', tag:'hot',   analysis:'4 goals — Dembélé outscoring even Mbappé. France beat Mexico in Last 16. QF vs Brazil.' },
  { rank:9, name:'Deniz Undav',      flag:'🇩🇪', club:'Stuttgart',      age:27, predGoals:2, actualGoals:3, actualAssists:2, form:'WWL', rating:8.2, confidence:45, odds:'+900', tag:'value', analysis:'3 goals, 2 assists — Germany beat Norway in Last 16. QF vs Spain. Key figure going forward.' },
  { rank:10,name:'Ismaila Sarr',     flag:'🇸🇳', club:'Marseille',      age:26, predGoals:2, actualGoals:3, actualAssists:1, form:'LLW', rating:7.8, confidence:35, odds:'+1200',tag:'tip',   analysis:'3 goals but Senegal eliminated. Exciting tournament but tournament over.' },
]

export const ASSISTS = [
  { rank:1, name:'Jude Bellingham',  flag:'🏴󠁧󠁢󠁥󠁮󠁧󠁿', club:'Real Madrid',    age:22, predAssists:5, actualAssists:2, actualGoals:1, form:'WDW', rating:9.1, confidence:72, odds:'+600', tag:'hot',   analysis:'2 assists, 1 goal. England beat Belgium in Last 16. England QF vs Argentina — key creative force.' },
  { rank:2, name:'Kevin De Bruyne',  flag:'🇧🇪', club:'Man City',       age:34, predAssists:5, actualAssists:2, actualGoals:1, form:'DDW', rating:8.9, confidence:65, odds:'+700', tag:'value', analysis:'2 assists. Belgium eliminated by England in Last 16. Outstanding tournament despite exit.' },
  { rank:3, name:'Pedri',            flag:'🇪🇸', club:'Barcelona',      age:23, predAssists:4, actualAssists:2, actualGoals:0, form:'DWW', rating:8.8, confidence:60, odds:'+800', tag:'tip',   analysis:'2 assists. Spain beat Australia in Last 16. Spain QF vs Germany — midfield engine.' },
  { rank:4, name:'Kylian Mbappé',    flag:'🇫🇷', club:'Real Madrid',    age:27, predAssists:4, actualAssists:2, actualGoals:4, form:'WWW', rating:9.2, confidence:58, odds:'+900', tag:'hot',   analysis:'2 assists alongside 4 goals. Complete player — France\'s engine in attack.' },
  { rank:5, name:'Bukayo Saka',      flag:'🏴󠁧󠁢󠁥󠁮󠁧󠁿', club:'Arsenal',       age:24, predAssists:4, actualAssists:1, actualGoals:1, form:'WDW', rating:9.1, confidence:58, odds:'+1000',tag:'tip',   analysis:'1 assist, 1 goal. England\'s most consistent creator — more in the knockouts.' },
  { rank:6, name:'Deniz Undav',      flag:'🇩🇪', club:'Stuttgart',      age:27, predAssists:2, actualAssists:2, actualGoals:3, form:'WWL', rating:8.2, confidence:45, odds:'+1100',tag:'value', analysis:'2 assists + 3 goals — Germany\'s complete number 9. Joint assist leader.' },
]

export const CLEANSHEETS = [
  { rank:1, name:'Mike Maignan',     flag:'🇫🇷', club:'AC Milan',       age:28, predCS:5, actualCS:2, form:'WWW', rating:9.0, confidence:70, odds:'+450', tag:'hot',   analysis:'2 clean sheets in group stage. France 9pts — conceded only 2 all tournament. Best GK so far.' },
  { rank:2, name:'Jordan Pickford',  flag:'🏴󠁧󠁢󠁥󠁮󠁧󠁿', club:'Everton',       age:32, predCS:4, actualCS:2, form:'WDW', rating:8.6, confidence:60, odds:'+600', tag:'value', analysis:'2 clean sheets. England beat Belgium in Last 16. QF vs Argentina — must-win for golden glove.' },
  { rank:3, name:'Alisson Becker',   flag:'🇧🇷', club:'Liverpool',      age:32, predCS:4, actualCS:1, form:'DWW', rating:8.9, confidence:58, odds:'+650', tag:'value', analysis:'1 clean sheet. Brazil beat USA in Last 16. QF vs France — biggest test yet.' },
  { rank:4, name:'Unai Simón',       flag:'🇪🇸', club:'Athletic Bilbao', age:27, predCS:4, actualCS:1, form:'DWW', rating:8.7, confidence:56, odds:'+700', tag:'tip',   analysis:'1 clean sheet. Spain beat Australia in Last 16. QF vs Germany — biggest match of tournament.' },
  { rank:5, name:'Manuel Neuer',     flag:'🇩🇪', club:'Bayern Munich',  age:40, predCS:3, actualCS:1, form:'WWL', rating:8.5, confidence:48, odds:'+900', tag:'tip',   analysis:'1 clean sheet. Germany beat Norway in Last 16. QF vs Spain — veteran commanding the box.' },
  { rank:6, name:'Bono',             flag:'🇲🇦', club:'Sevilla',        age:33, predCS:3, actualCS:1, form:'DWW', rating:8.3, confidence:42, odds:'+1100',tag:'tip',   analysis:'1 clean sheet. Morocco eliminated by Netherlands in Last 16. Excellent tournament debut.' },
]

// Live tournament leaders (Golden Boot race)
export const GOLDEN_BOOT_LIVE = [
  { name:'Lionel Messi',    flag:'🇦🇷', goals:6, assists:0, team:'Argentina',  status:'QF' },
  { name:'Kylian Mbappé',   flag:'🇫🇷', goals:6, assists:2, team:'France',     status:'QF' },
  { name:'Ousmane Dembélé', flag:'🇫🇷', goals:4, assists:1, team:'France',     status:'QF' },
  { name:'Vinicius Jr.',    flag:'🇧🇷', goals:4, assists:1, team:'Brazil',     status:'QF' },
  { name:'Erling Haaland',  flag:'🇳🇴', goals:5, assists:0, team:'Norway',     status:'OUT' },
  { name:'Deniz Undav',     flag:'🇩🇪', goals:3, assists:2, team:'Germany',    status:'QF' },
  { name:'Johan Manzambi',  flag:'🇨🇭', goals:3, assists:1, team:'Switzerland',status:'OUT' },
  { name:'Ismaila Sarr',    flag:'🇸🇳', goals:3, assists:1, team:'Senegal',    status:'OUT' },
  { name:'Brian Brobbey',   flag:'🇳🇱', goals:3, assists:0, team:'Netherlands',status:'QF' },
  { name:'Matheus Cunha',   flag:'🇧🇷', goals:3, assists:0, team:'Brazil',     status:'QF' },
]

export const GOLDEN_ASSIST_LIVE = [
  { name:'Kylian Mbappé',   flag:'🇫🇷', assists:2, goals:6, team:'France',     status:'QF' },
  { name:'Deniz Undav',     flag:'🇩🇪', assists:2, goals:3, team:'Germany',    status:'QF' },
  { name:'Jude Bellingham', flag:'🏴󠁧󠁢󠁥󠁮󠁧󠁿', assists:2, goals:1, team:'England',    status:'QF' },
  { name:'Kevin De Bruyne', flag:'🇧🇪', assists:2, goals:1, team:'Belgium',    status:'OUT' },
  { name:'Pedri',           flag:'🇪🇸', assists:2, goals:0, team:'Spain',      status:'QF' },
  { name:'Lamine Yamal',    flag:'🇪🇸', assists:2, goals:1, team:'Spain',      status:'QF' },
  { name:'Vinicius Jr.',    flag:'🇧🇷', assists:1, goals:4, team:'Brazil',     status:'QF' },
  { name:'Bukayo Saka',     flag:'🏴󠁧󠁢󠁥󠁮󠁧󠁿', assists:1, goals:1, team:'England',    status:'QF' },
  { name:'Ousmane Dembélé', flag:'🇫🇷', assists:1, goals:4, team:'France',     status:'QF' },
  { name:'Ismaila Sarr',    flag:'🇸🇳', assists:1, goals:3, team:'Senegal',    status:'OUT' },
]
