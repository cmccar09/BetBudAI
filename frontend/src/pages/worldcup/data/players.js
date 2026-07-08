// actualGoals/actualAssists/actualCS updated to July 1 2026
// Source: ESPN fifa.world API (automated daily at 06:00 UTC via world-cup-scraper Lambda)

export const SCORERS = [
  { rank:1, name:'Kylian Mbappé',   flag:'🇫🇷', club:'Real Madrid',    age:27, predGoals:7, actualGoals:6, actualAssists:2, form:'WWW', rating:9.6, confidence:88, odds:'+200', tag:'hot',   analysis:'6 goals — brace vs Sweden (Jun 30, 3-0). Joint Golden Boot leader with Messi. France R16 vs Paraguay.' },
  { rank:2, name:'Harry Kane',       flag:'🏴󠁧󠁢󠁥󠁮󠁧󠁿', club:'Bayern Munich',  age:32, predGoals:6, actualGoals:2, actualAssists:1, form:'WDW', rating:9.0, confidence:65, odds:'+400', tag:'value', analysis:'2 goals through group stage. England were conservative vs Ghana — expect more in R32.' },
  { rank:3, name:'Erling Haaland',   flag:'🇳🇴', club:'Man City',       age:25, predGoals:6, actualGoals:5, actualAssists:0, form:'WWW', rating:9.3, confidence:70, odds:'+350', tag:'hot',   analysis:'5 goals — scored vs Ivory Coast (R32 Jun 30). Norway in R16. Haaland is Mbappé\'s closest rival.' },
  { rank:4, name:'Julián Álvarez',   flag:'🇦🇷', club:'Atlético Madrid', age:24, predGoals:5, actualGoals:2, actualAssists:1, form:'WWW', rating:8.8, confidence:55, odds:'+700', tag:'value', analysis:'2 goals alongside Messi. Argentina perfect group — Álvarez feeds off Messi service.' },
  { rank:5, name:'Lamine Yamal',     flag:'🇪🇸', club:'Barcelona',      age:18, predGoals:5, actualGoals:1, actualAssists:2, form:'DWW', rating:9.0, confidence:52, odds:'+800', tag:'tip',   analysis:'1 goal, 2 assists. Spain improve as tournament goes on. Spain vs Austria in R32.' },
  { rank:6, name:'Vinicius Jr.',     flag:'🇧🇷', club:'Real Madrid',    age:24, predGoals:5, actualGoals:4, actualAssists:1, form:'DWW', rating:8.9, confidence:50, odds:'+900', tag:'tip',   analysis:'4 goals in group stage — Brazil\'s star player has been electric. R32 vs Japan next.' },
  // Other tournament leaders not in original predictions
  { rank:2, name:'Lionel Messi',     flag:'🇦🇷', club:'Inter Miami',    age:38, predGoals:3, actualGoals:6, actualAssists:0, form:'WWW', rating:9.5, confidence:85, odds:'+280', tag:'hot',   analysis:'6 goals — JOINT GOLDEN BOOT with Mbappé. Argentina R32 vs Cape Verde (Jul 3). One last dance.' },
  { rank:8, name:'Ousmane Dembélé',  flag:'🇫🇷', club:'PSG',            age:28, predGoals:3, actualGoals:4, actualAssists:1, form:'WWW', rating:8.6, confidence:60, odds:'+500', tag:'hot',   analysis:'4 goals — Dembélé outscoring even Mbappé. France\'s surprise top scorer.' },
  { rank:9, name:'Deniz Undav',      flag:'🇩🇪', club:'Stuttgart',      age:27, predGoals:2, actualGoals:3, actualAssists:2, form:'WWL', rating:8.2, confidence:45, odds:'+900', tag:'value', analysis:'3 goals, 2 assists — Germany\'s clinical finisher. Key in R32 vs Paraguay.' },
  { rank:10,name:'Ismaila Sarr',     flag:'🇸🇳', club:'Marseille',      age:26, predGoals:2, actualGoals:3, actualAssists:1, form:'LLW', rating:7.8, confidence:35, odds:'+1200',tag:'tip',   analysis:'3 goals but Senegal eliminated. Exciting tournament but tournament over.' },
]

export const ASSISTS = [
  { rank:1, name:'Jude Bellingham',  flag:'🏴󠁧󠁢󠁥󠁮󠁧󠁿', club:'Real Madrid',    age:22, predAssists:5, actualAssists:2, actualGoals:1, form:'WDW', rating:9.1, confidence:72, odds:'+600', tag:'hot',   analysis:'2 assists through group stage. England\'s creative hub — more to come in R32 vs DR Congo.' },
  { rank:2, name:'Kevin De Bruyne',  flag:'🇧🇪', club:'Man City',       age:34, predAssists:5, actualAssists:2, actualGoals:1, form:'DDW', rating:8.9, confidence:65, odds:'+700', tag:'value', analysis:'2 assists. Belgium finally clicked 5-1 vs NZ. De Bruyne back to his best in R32.' },
  { rank:3, name:'Pedri',            flag:'🇪🇸', club:'Barcelona',      age:23, predAssists:4, actualAssists:2, actualGoals:0, form:'DWW', rating:8.8, confidence:60, odds:'+800', tag:'tip',   analysis:'2 assists. Spain playing better as tournament progresses. Spain vs Austria in R32.' },
  { rank:4, name:'Kylian Mbappé',    flag:'🇫🇷', club:'Real Madrid',    age:27, predAssists:4, actualAssists:2, actualGoals:4, form:'WWW', rating:9.2, confidence:58, odds:'+900', tag:'hot',   analysis:'2 assists alongside 4 goals. Complete player — France\'s engine in attack.' },
  { rank:5, name:'Bukayo Saka',      flag:'🏴󠁧󠁢󠁥󠁮󠁧󠁿', club:'Arsenal',       age:24, predAssists:4, actualAssists:1, actualGoals:1, form:'WDW', rating:9.1, confidence:58, odds:'+1000',tag:'tip',   analysis:'1 assist, 1 goal. England\'s most consistent creator — more in the knockouts.' },
  { rank:6, name:'Deniz Undav',      flag:'🇩🇪', club:'Stuttgart',      age:27, predAssists:2, actualAssists:2, actualGoals:3, form:'WWL', rating:8.2, confidence:45, odds:'+1100',tag:'value', analysis:'2 assists + 3 goals — Germany\'s complete number 9. Joint assist leader.' },
]

export const CLEANSHEETS = [
  { rank:1, name:'Mike Maignan',     flag:'🇫🇷', club:'AC Milan',       age:28, predCS:5, actualCS:2, form:'WWW', rating:9.0, confidence:70, odds:'+450', tag:'hot',   analysis:'2 clean sheets in group stage. France 9pts — conceded only 2 all tournament. Best GK so far.' },
  { rank:2, name:'Jordan Pickford',  flag:'🏴󠁧󠁢󠁥󠁮󠁧󠁿', club:'Everton',       age:32, predCS:4, actualCS:2, form:'WDW', rating:8.6, confidence:60, odds:'+600', tag:'value', analysis:'2 clean sheets. England conceded only 2. Solid throughout — R32 vs DR Congo next.' },
  { rank:3, name:'Alisson Becker',   flag:'🇧🇷', club:'Liverpool',      age:32, predCS:4, actualCS:1, form:'DWW', rating:8.9, confidence:58, odds:'+650', tag:'value', analysis:'1 clean sheet. Brazil beat Scotland 3-0 but drew 1-1 with Morocco in opener.' },
  { rank:4, name:'Unai Simón',       flag:'🇪🇸', club:'Athletic Bilbao', age:27, predCS:4, actualCS:1, form:'DWW', rating:8.7, confidence:56, odds:'+700', tag:'tip',   analysis:'1 clean sheet (vs Uruguay 1-0). Spain drew 0-0 with Cape Verde — Simon was barely tested.' },
  { rank:5, name:'Manuel Neuer',     flag:'🇩🇪', club:'Bayern Munich',  age:40, predCS:3, actualCS:1, form:'WWL', rating:8.5, confidence:48, odds:'+900', tag:'tip',   analysis:'1 clean sheet. Germany\'s 7-1 win vs Curaçao but shocked by Ecuador in MD3. Still in R32.' },
  { rank:6, name:'Bono',             flag:'🇲🇦', club:'Sevilla',        age:33, predCS:3, actualCS:1, form:'DWW', rating:8.3, confidence:42, odds:'+1100',tag:'tip',   analysis:'1 clean sheet. Morocco 2nd from Group C with 7pts. Faces Netherlands in R32.' },
]

// Live tournament leaders (Golden Boot race)
export const GOLDEN_BOOT_LIVE = [
  { name:'Lionel Messi',    flag:'🇦🇷', goals:5, assists:0, team:'Argentina',  status:'R32' },
  { name:'Kylian Mbappé',   flag:'🇫🇷', goals:4, assists:2, team:'France',     status:'R32' },
  { name:'Ousmane Dembélé', flag:'🇫🇷', goals:4, assists:1, team:'France',     status:'R32' },
  { name:'Vinicius Jr.',    flag:'🇧🇷', goals:4, assists:1, team:'Brazil',     status:'R32' },
  { name:'Erling Haaland',  flag:'🇳🇴', goals:4, assists:0, team:'Norway',     status:'R32' },
  { name:'Deniz Undav',     flag:'🇩🇪', goals:3, assists:2, team:'Germany',    status:'R32' },
  { name:'Johan Manzambi',  flag:'🇨🇭', goals:3, assists:1, team:'Switzerland',status:'R32' },
  { name:'Ismaila Sarr',    flag:'🇸🇳', goals:3, assists:1, team:'Senegal',    status:'OUT' },
  { name:'Brian Brobbey',   flag:'🇳🇱', goals:3, assists:0, team:'Netherlands',status:'R32' },
  { name:'Matheus Cunha',   flag:'🇧🇷', goals:3, assists:0, team:'Brazil',     status:'R32' },
]

export const GOLDEN_ASSIST_LIVE = [
  { name:'Kylian Mbappé',   flag:'🇫🇷', assists:2, goals:4, team:'France',     status:'R32' },
  { name:'Deniz Undav',     flag:'🇩🇪', assists:2, goals:3, team:'Germany',    status:'R32' },
  { name:'Jude Bellingham', flag:'🏴󠁧󠁢󠁥󠁮󠁧󠁿', assists:2, goals:1, team:'England',    status:'R32' },
  { name:'Kevin De Bruyne', flag:'🇧🇪', assists:2, goals:1, team:'Belgium',    status:'R32' },
  { name:'Pedri',           flag:'🇪🇸', assists:2, goals:0, team:'Spain',      status:'R32' },
  { name:'Lamine Yamal',    flag:'🇪🇸', assists:2, goals:1, team:'Spain',      status:'R32' },
  { name:'Vinicius Jr.',    flag:'🇧🇷', assists:1, goals:4, team:'Brazil',     status:'R32' },
  { name:'Bukayo Saka',     flag:'🏴󠁧󠁢󠁥󠁮󠁧󠁿', assists:1, goals:1, team:'England',    status:'R32' },
  { name:'Ousmane Dembélé', flag:'🇫🇷', assists:1, goals:4, team:'France',     status:'R32' },
  { name:'Ismaila Sarr',    flag:'🇸🇳', assists:1, goals:3, team:'Senegal',    status:'OUT' },
]
