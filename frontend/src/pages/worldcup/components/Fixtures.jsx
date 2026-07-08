import { useState } from 'react'

const FLAGS = {
  'Mexico': '🇲🇽', 'South Africa': '🇿🇦', 'South Korea': '🇰🇷', 'Czechia': '🇨🇿',
  'Canada': '🇨🇦', 'Bosnia & Herz.': '🇧🇦', 'Qatar': '🇶🇦', 'Switzerland': '🇨🇭',
  'Brazil': '🇧🇷', 'Morocco': '🇲🇦', 'Haiti': '🇭🇹', 'Scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
  'United States': '🇺🇸', 'Paraguay': '🇵🇾', 'Australia': '🇦🇺', 'Türkiye': '🇹🇷',
  'Germany': '🇩🇪', 'Curaçao': '🇨🇼', 'Ivory Coast': '🇨🇮', 'Ecuador': '🇪🇨',
  'Netherlands': '🇳🇱', 'Japan': '🇯🇵', 'Sweden': '🇸🇪', 'Tunisia': '🇹🇳',
  'Belgium': '🇧🇪', 'Egypt': '🇪🇬', 'Iran': '🇮🇷', 'New Zealand': '🇳🇿',
  'Spain': '🇪🇸', 'Cape Verde': '🇨🇻', 'Saudi Arabia': '🇸🇦', 'Uruguay': '🇺🇾',
  'France': '🇫🇷', 'Senegal': '🇸🇳', 'Iraq': '🇮🇶', 'Norway': '🇳🇴',
  'Argentina': '🇦🇷', 'Algeria': '🇩🇿', 'Austria': '🇦🇹', 'Jordan': '🇯🇴',
  'Portugal': '🇵🇹', 'DR Congo': '🇨🇩', 'Uzbekistan': '🇺🇿', 'Colombia': '🇨🇴',
  'England': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'Croatia': '🇭🇷', 'Ghana': '🇬🇭', 'Panama': '🇵🇦',
}

// All dates use US Eastern (ET) as the date field — app calculates "today" in ET.
// Times shown in BST (UK) for display. ET = BST - 5h.
// Source: Yahoo Sports / FIFA official schedule verified 2026-06-18.
const DEMO_FIXTURES = [
  // ── MD1 — all verified from Yahoo Sports / FIFA (dates = US Eastern) ────
  // Jun 11
  { id:1,  date:'2026-06-11',time:'02:00',home:'Mexico',        away:'South Africa',  group:'Group A',hS:2, aS:0, status:'FT',predH:2,predA:0,prob:[65,20,15],venue:'Estadio Azteca, Mexico City',        btts:{pred:'No',conf:68}, ou25:{pred:'Under',conf:58},reasoning:'Hosts dominated from the off — perfect prediction.' },
  // Jun 12
  { id:2,  date:'2026-06-12',time:'02:00',home:'South Korea',   away:'Czechia',       group:'Group A',hS:2, aS:1, status:'FT',predH:1,predA:1,prob:[30,35,35],venue:'Estadio Akron, Guadalajara',          btts:{pred:'Yes',conf:55},ou25:{pred:'Under',conf:52},reasoning:'South Korea won 2-1 — our draw prediction was wrong.' },
  { id:3,  date:'2026-06-12',time:'21:00',home:'United States', away:'Paraguay',      group:'Group D',hS:4, aS:1, status:'FT',predH:2,predA:1,prob:[58,22,20],venue:'SoFi Stadium, Inglewood CA',          btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:56}, reasoning:'USA demolished Paraguay 4-1 — direction right, margin underestimated.' },
  { id:4,  date:'2026-06-12',time:'22:00',home:'Canada',        away:'Bosnia & Herz.',group:'Group B',hS:1, aS:1, status:'FT',predH:1,predA:1,prob:[40,35,25],venue:'BMO Field, Toronto',                  btts:{pred:'Yes',conf:55},ou25:{pred:'Under',conf:52},reasoning:'Tight cagey opener ended level as predicted.' },
  // Jun 13
  { id:5,  date:'2026-06-13',time:'18:00',home:'Switzerland',   away:'Qatar',         group:'Group B',hS:1, aS:1, status:'FT',predH:2,predA:1,prob:[60,25,15],venue:"Levi's Stadium, Santa Clara",         btts:{pred:'Yes',conf:52},ou25:{pred:'Over',conf:54}, reasoning:'Qatar held Switzerland to a surprise 1-1 draw.' },
  { id:6,  date:'2026-06-13',time:'18:00',home:'Brazil',        away:'Morocco',       group:'Group C',hS:1, aS:1, status:'FT',predH:2,predA:1,prob:[55,25,20],venue:'MetLife Stadium, East Rutherford NJ', btts:{pred:'Yes',conf:55},ou25:{pred:'Over',conf:52}, reasoning:'Brazil held — Morocco proved they are a match for the world-class side.' },
  // Jun 14
  { id:7,  date:'2026-06-14',time:'18:00',home:'Scotland',      away:'Haiti',         group:'Group C',hS:1, aS:0, status:'FT',predH:2,predA:0,prob:[60,25,15],venue:'Gillette Stadium, Foxborough MA',     btts:{pred:'No',conf:60}, ou25:{pred:'Under',conf:55},reasoning:'Scotland ground out a tight 1-0 win.' },
  { id:8,  date:'2026-06-14',time:'18:00',home:'Australia',     away:'Türkiye',       group:'Group D',hS:2, aS:0, status:'FT',predH:1,predA:1,prob:[30,30,40],venue:'BC Place, Vancouver',                 btts:{pred:'Yes',conf:56},ou25:{pred:'Over',conf:53}, reasoning:'Australia dominated — Türkiye failed to threaten.' },
  { id:9,  date:'2026-06-14',time:'21:00',home:'Germany',       away:'Curaçao',       group:'Group E',hS:7, aS:1, status:'FT',predH:5,predA:0,prob:[95,4,1],  venue:'NRG Stadium, Houston',                btts:{pred:'No',conf:88}, ou25:{pred:'Over',conf:92}, reasoning:'Germany 7-1 — even bigger than our 5-0 prediction.' },
  { id:10, date:'2026-06-14',time:'21:00',home:'Ivory Coast',   away:'Ecuador',       group:'Group E',hS:1, aS:0, status:'FT',predH:1,predA:1,prob:[42,30,28],venue:'NRG Stadium, Houston',                btts:{pred:'Yes',conf:52},ou25:{pred:'Under',conf:54},reasoning:'Ivory Coast nicked it with a narrow win.' },
  { id:11, date:'2026-06-14',time:'18:00',home:'Netherlands',   away:'Japan',         group:'Group F',hS:2, aS:2, status:'FT',predH:2,predA:1,prob:[50,25,25],venue:'AT&T Stadium, Arlington TX',          btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:56}, reasoning:'Japan equalised late — Netherlands held to a draw.' },
  { id:12, date:'2026-06-14',time:'21:00',home:'Sweden',        away:'Tunisia',       group:'Group F',hS:5, aS:1, status:'FT',predH:2,predA:0,prob:[62,22,16],venue:'BC Place, Vancouver',                 btts:{pred:'No',conf:60}, ou25:{pred:'Over',conf:65}, reasoning:'Sweden hammered Tunisia 5-1 — Group F leader.' },
  // Jun 15
  { id:13, date:'2026-06-15',time:'17:00',home:'Spain',         away:'Cape Verde',    group:'Group H',hS:0, aS:0, status:'FT',predH:3,predA:0,prob:[87,10,3], venue:'Mercedes-Benz Stadium, Atlanta',      btts:{pred:'No',conf:75}, ou25:{pred:'Over',conf:80}, reasoning:'Shock 0-0 — Cape Verde defended superbly to stun Spain.' },
  { id:14, date:'2026-06-15',time:'20:00',home:'Belgium',       away:'Egypt',         group:'Group G',hS:1, aS:1, status:'FT',predH:2,predA:1,prob:[60,22,18],venue:'Lumen Field, Seattle',                btts:{pred:'Yes',conf:55},ou25:{pred:'Over',conf:54}, reasoning:'Belgium failed to hold their lead.' },
  { id:15, date:'2026-06-15',time:'20:00',home:'Saudi Arabia',  away:'Uruguay',       group:'Group H',hS:1, aS:1, status:'FT',predH:1,predA:2,prob:[25,30,45],venue:'SoFi Stadium, Inglewood CA',          btts:{pred:'Yes',conf:55},ou25:{pred:'Over',conf:52}, reasoning:'Saudi Arabia dug deep for a surprise point.' },
  // Jun 16
  { id:16, date:'2026-06-16',time:'20:00',home:'Iran',          away:'New Zealand',   group:'Group G',hS:2, aS:2, status:'FT',predH:2,predA:0,prob:[55,25,20],venue:'Lumen Field, Seattle',                btts:{pred:'No',conf:58}, ou25:{pred:'Over',conf:55}, reasoning:'New Zealand levelled twice — pulsating Group G opener.' },
  { id:17, date:'2026-06-16',time:'20:00',home:'France',        away:'Senegal',       group:'Group I',hS:3, aS:1, status:'FT',predH:2,predA:1,prob:[55,22,23],venue:'MetLife Stadium, East Rutherford NJ', btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:56}, reasoning:'France won 3-1 — direction correct.' },
  { id:18, date:'2026-06-16',time:'20:00',home:'Iraq',          away:'Norway',        group:'Group I',hS:1, aS:4, status:'FT',predH:0,predA:3,prob:[12,20,68],venue:"Levi's Stadium, Santa Clara",         btts:{pred:'Yes',conf:60},ou25:{pred:'Over',conf:72}, reasoning:'Norway ran riot — 4-1 in Group I.' },
  { id:19, date:'2026-06-16',time:'13:00',home:'Argentina',     away:'Algeria',       group:'Group J',hS:3, aS:0, status:'FT',predH:3,predA:0,prob:[82,12,6], venue:'MetLife Stadium, East Rutherford NJ', btts:{pred:'No',conf:72}, ou25:{pred:'Over',conf:76}, reasoning:'World champions too strong — perfect prediction.' },
  { id:20, date:'2026-06-16',time:'13:00',home:'Austria',       away:'Jordan',        group:'Group J',hS:3, aS:1, status:'FT',predH:2,predA:0,prob:[60,22,18],venue:'AT&T Stadium, Arlington TX',          btts:{pred:'No',conf:62}, ou25:{pred:'Over',conf:60}, reasoning:'Austria won comfortably — Jordan outclassed.' },
  // Jun 17
  { id:21, date:'2026-06-17',time:'16:00',home:'Portugal',      away:'DR Congo',      group:'Group K',hS:1, aS:1, status:'FT',predH:3,predA:0,prob:[80,14,6], venue:'Rose Bowl, Pasadena CA',              btts:{pred:'No',conf:70}, ou25:{pred:'Over',conf:78}, reasoning:'Shock — DR Congo held Portugal to a 1-1 draw.' },
  { id:22, date:'2026-06-17',time:'16:00',home:'Uzbekistan',    away:'Colombia',      group:'Group K',hS:1, aS:3, status:'FT',predH:0,predA:2,prob:[20,25,55],venue:'Hard Rock Stadium, Miami FL',         btts:{pred:'Yes',conf:60},ou25:{pred:'Over',conf:65}, reasoning:'Colombia dominant — Uzbekistan outclassed 3-1.' },
  { id:23, date:'2026-06-17',time:'13:00',home:'England',       away:'Croatia',       group:'Group L',hS:4, aS:2, status:'FT',predH:2,predA:0,prob:[68,20,12],venue:'AT&T Stadium, Arlington TX',          btts:{pred:'No',conf:62}, ou25:{pred:'Under',conf:54},reasoning:'England ran riot — 4-2 in an open thriller.' },
  { id:24, date:'2026-06-17',time:'16:00',home:'Ghana',         away:'Panama',        group:'Group L',hS:1, aS:0, status:'FT',predH:2,predA:0,prob:[55,25,20],venue:'SoFi Stadium, Inglewood CA',          btts:{pred:'No',conf:60}, ou25:{pred:'Under',conf:55},reasoning:'Ghana ground out a tight Group L opener.' },
  // ── MD2 — predictions recalibrated from MD1 scoring data ─────────────────
  // Avg 3.2 goals/game in MD1. Over 2.5 hit 62%. Big teams scoring heavily
  // (USA 4, Germany 7, Sweden 5, England 4, Norway 4). Brazil/Spain/Portugal
  // struggled. Draws common between evenly matched sides (7 in 24 MD1 games).
  // Jun 18
  { id:25, date:'2026-06-18',time:'17:00',home:'Czechia',       away:'South Africa',  group:'Group A',hS:null,aS:null,status:'NS',predH:2,predA:0,prob:[60,22,18],venue:'Mercedes-Benz Stadium, Atlanta',     btts:{pred:'No',conf:65}, ou25:{pred:'Under',conf:58},reasoning:'Czechia lost MD1 but South Africa have 0 goals — Czechia should win without conceding.' },
  { id:26, date:'2026-06-18',time:'20:00',home:'Switzerland',   away:'Bosnia & Herz.',group:'Group B',hS:null,aS:null,status:'NS',predH:1,predA:1,prob:[38,34,28],venue:'SoFi Stadium, Inglewood CA',          btts:{pred:'Yes',conf:58},ou25:{pred:'Under',conf:55}, reasoning:'Both drew 1-1 in MD1 — evenly matched, another tight draw likely.' },
  { id:27, date:'2026-06-18',time:'23:00',home:'Canada',        away:'Qatar',         group:'Group B',hS:null,aS:null,status:'NS',predH:2,predA:1,prob:[60,22,18],venue:'BC Place, Vancouver',                 btts:{pred:'Yes',conf:62},ou25:{pred:'Over',conf:60}, reasoning:'Canada at home — both teams showed they can score in MD1.' },
  { id:28, date:'2026-06-18',time:'02:00',home:'Mexico',        away:'South Korea',   group:'Group A',hS:null,aS:null,status:'NS',predH:2,predA:1,prob:[52,25,23],venue:'Estadio Akron, Guadalajara',          btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'Mexico won 2-0, South Korea won 2-1 — both attack-minded, winner seals Group A top spot.' },
  // Jun 19
  { id:29, date:'2026-06-19',time:'20:00',home:'United States', away:'Australia',     group:'Group D',hS:2,aS:0,status:'FT',predH:2,predA:1,prob:[48,22,30],venue:'Lumen Field, Seattle',                btts:{pred:'Yes',conf:65},ou25:{pred:'Over',conf:68}, reasoning:'USA clinical — Australia could not break them down. 2-0.' },
  { id:30, date:'2026-06-19',time:'23:00',home:'Scotland',      away:'Morocco',       group:'Group C',hS:0,aS:1,status:'FT',predH:1,predA:1,prob:[32,35,33],venue:'Gillette Stadium, Foxborough MA',     btts:{pred:'Yes',conf:58},ou25:{pred:'Under',conf:55}, reasoning:'Morocco won 0-1 — Scotland lead was short-lived. Upset.' },
  { id:31, date:'2026-06-19',time:'01:30',home:'Brazil',        away:'Haiti',         group:'Group C',hS:3,aS:0,status:'FT',predH:2,predA:0,prob:[85,10,5], venue:'Lincoln Financial Field, Philadelphia',btts:{pred:'No',conf:72}, ou25:{pred:'Over',conf:72}, reasoning:'Brazil 3-0 Haiti — sealed qualification comfortably.' },
  { id:32, date:'2026-06-19',time:'04:00',home:'Türkiye',       away:'Paraguay',      group:'Group D',hS:0,aS:1,status:'FT',predH:2,predA:1,prob:[50,25,25],venue:"Levi's Stadium, Santa Clara",         btts:{pred:'Yes',conf:55},ou25:{pred:'Over',conf:56}, reasoning:'UPSET — Paraguay beat Turkey 0-1 despite being underdogs.' },
  // Jun 20
  { id:33, date:'2026-06-20',time:'18:00',home:'Netherlands',   away:'Sweden',        group:'Group F',hS:5,aS:1,status:'FT',predH:2,predA:1,prob:[45,22,33],venue:'NRG Stadium, Houston',                btts:{pred:'Yes',conf:65},ou25:{pred:'Over',conf:68}, reasoning:'Netherlands demolished Sweden 5-1 — total statement after 2-2 draw.' },
  { id:34, date:'2026-06-20',time:'21:00',home:'Germany',       away:'Ivory Coast',   group:'Group E',hS:2,aS:1,status:'FT',predH:4,predA:1,prob:[70,18,12],venue:'BMO Field, Toronto',                  btts:{pred:'Yes',conf:70},ou25:{pred:'Over',conf:85}, reasoning:'Germany 2-1 Ivory Coast — tougher than expected.' },
  { id:35, date:'2026-06-20',time:'01:00',home:'Ecuador',       away:'Curaçao',       group:'Group E',hS:0,aS:0,status:'FT',predH:3,predA:0,prob:[78,15,7], venue:'Arrowhead Stadium, Kansas City MO',   btts:{pred:'No',conf:72}, ou25:{pred:'Over',conf:75}, reasoning:'SHOCK — Ecuador 0-0 Curaçao. Ecuador crash out.' },
  { id:36, date:'2026-06-20',time:'05:00',home:'Tunisia',       away:'Japan',         group:'Group F',hS:0,aS:4,status:'FT',predH:0,predA:2,prob:[18,25,57],venue:'Estadio BBVA, Monterrey',             btts:{pred:'No',conf:60}, ou25:{pred:'Under',conf:55},reasoning:'Japan 4-0 Tunisia — clinical, sealed top spot.' },
  // Jun 21
  { id:37, date:'2026-06-21',time:'17:00',home:'Spain',         away:'Saudi Arabia',  group:'Group H',hS:4,aS:0,status:'FT',predH:2,predA:0,prob:[65,20,15],venue:'Mercedes-Benz Stadium, Atlanta',      btts:{pred:'No',conf:62}, ou25:{pred:'Under',conf:55},reasoning:'Spain 4-0 Saudi Arabia — back to their devastating best.' },
  { id:38, date:'2026-06-21',time:'20:00',home:'Belgium',       away:'Iran',          group:'Group G',hS:0,aS:0,status:'FT',predH:2,predA:1,prob:[58,22,20],venue:'SoFi Stadium, Inglewood CA',          btts:{pred:'Yes',conf:60},ou25:{pred:'Over',conf:60}, reasoning:'Belgium 0-0 Iran — Belgium cannot score. Shocking form.' },
  { id:39, date:'2026-06-21',time:'23:00',home:'Uruguay',       away:'Cape Verde',    group:'Group H',hS:2,aS:2,status:'FT',predH:2,predA:0,prob:[62,22,16],venue:'Hard Rock Stadium, Miami FL',         btts:{pred:'No',conf:62}, ou25:{pred:'Over',conf:58}, reasoning:'Uruguay 2-2 Cape Verde — Cape Verde incredible again, drew with Spain 0-0 and Uruguay 2-2.' },
  { id:40, date:'2026-06-21',time:'02:00',home:'New Zealand',   away:'Egypt',         group:'Group G',hS:3,aS:1,status:'FT',predH:1,predA:2,prob:[28,30,42],venue:'BC Place, Vancouver',                 btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:58}, reasoning:'Egypt 3-1 New Zealand — Egypt through.' },
  // Jun 22
  { id:41, date:'2026-06-22',time:'18:00',home:'Argentina',     away:'Austria',       group:'Group J',hS:2,aS:0,status:'FT',predH:2,predA:1,prob:[60,22,18],venue:'AT&T Stadium, Arlington TX',          btts:{pred:'Yes',conf:62},ou25:{pred:'Over',conf:65}, reasoning:'Argentina 2-0 Austria — controlled, clean sheet.' },
  { id:42, date:'2026-06-22',time:'22:00',home:'France',        away:'Iraq',          group:'Group I',hS:3,aS:0,status:'FT',predH:3,predA:0,prob:[88,9,3],  venue:'Lincoln Financial Field, Philadelphia',btts:{pred:'No',conf:78}, ou25:{pred:'Over',conf:80}, reasoning:'France 3-0 Iraq — perfect prediction.' },
  { id:43, date:'2026-06-22',time:'01:00',home:'Norway',        away:'Senegal',       group:'Group I',hS:3,aS:2,status:'FT',predH:2,predA:0,prob:[65,20,15],venue:'MetLife Stadium, East Rutherford NJ', btts:{pred:'No',conf:65}, ou25:{pred:'Over',conf:62}, reasoning:'Norway 3-2 Senegal — thrilling, Norway too strong overall.' },
  { id:44, date:'2026-06-22',time:'04:00',home:'Jordan',        away:'Algeria',       group:'Group J',hS:1,aS:2,status:'FT',predH:0,predA:1,prob:[22,28,50],venue:"Levi's Stadium, Santa Clara",         btts:{pred:'No',conf:58}, ou25:{pred:'Under',conf:56},reasoning:'Jordan 1-2 Algeria — Algeria through, both scored as expected.' },
  // ── MD3 — final group games ───────────────────────────────────────────────
  // Jun 23
  { id:45, date:'2026-06-23',time:'18:00',home:'Portugal',      away:'Uzbekistan',    group:'Group K',hS:5,aS:0,status:'FT',predH:2,predA:0,prob:[75,15,10],venue:'NRG Stadium, Houston',                btts:{pred:'No',conf:68}, ou25:{pred:'Over',conf:65}, reasoning:'Portugal 5-0 Uzbekistan — true quality finally unleashed.' },
  { id:46, date:'2026-06-23',time:'21:00',home:'England',       away:'Ghana',         group:'Group L',hS:0,aS:0,status:'FT',predH:3,predA:1,prob:[60,20,20],venue:'Gillette Stadium, Foxborough MA',     btts:{pred:'Yes',conf:65},ou25:{pred:'Over',conf:72}, reasoning:'0-0 — England were poor. Ghana proved extremely hard to beat.' },
  { id:47, date:'2026-06-23',time:'00:00',home:'Panama',        away:'Croatia',       group:'Group L',hS:0,aS:1,status:'FT',predH:0,predA:2,prob:[12,22,66],venue:'BMO Field, Toronto',                  btts:{pred:'No',conf:62}, ou25:{pred:'Under',conf:55},reasoning:'Panama 0-1 Croatia — Croatia scrape through. Panama still goalless all tournament.' },
  { id:48, date:'2026-06-23',time:'03:00',home:'Colombia',      away:'DR Congo',      group:'Group K',hS:1,aS:0,status:'FT',predH:2,predA:0,prob:[68,18,14],venue:'Estadio Akron, Guadalajara',          btts:{pred:'No',conf:65}, ou25:{pred:'Over',conf:60}, reasoning:'Colombia 1-0 DR Congo — through, DR Congo made them work.' },
  // Jun 24 (simultaneous final group games)
  { id:49, date:'2026-06-24',time:'20:00',home:'Switzerland',   away:'Canada',        group:'Group B',hS:2,aS:1,status:'FT',predH:2,predA:1,prob:[52,25,23],venue:'BC Place, Vancouver',                 btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'Switzerland 2-1 Canada — topped Group B.' },
  { id:50, date:'2026-06-24',time:'20:00',home:'Bosnia & Herz.',away:'Qatar',         group:'Group B',hS:3,aS:1,status:'FT',predH:2,predA:0,prob:[55,25,20],venue:'Lumen Field, Seattle',                btts:{pred:'No',conf:60}, ou25:{pred:'Under',conf:56},reasoning:'Bosnia 3-1 Qatar — advance as best third-place team.' },
  { id:51, date:'2026-06-24',time:'23:00',home:'Scotland',      away:'Brazil',        group:'Group C',hS:0,aS:3,status:'FT',predH:1,predA:2,prob:[28,25,47],venue:'Hard Rock Stadium, Miami FL',         btts:{pred:'Yes',conf:62},ou25:{pred:'Over',conf:65}, reasoning:'Scotland 0-3 Brazil — Brazil showed their real quality when it mattered.' },
  { id:52, date:'2026-06-24',time:'23:00',home:'Morocco',       away:'Haiti',         group:'Group C',hS:4,aS:2,status:'FT',predH:2,predA:0,prob:[80,14,6], venue:'Mercedes-Benz Stadium, Atlanta',      btts:{pred:'No',conf:68}, ou25:{pred:'Over',conf:65}, reasoning:'Morocco 4-2 Haiti — both teams through from Group C.' },
  { id:53, date:'2026-06-24',time:'02:00',home:'Czechia',       away:'Mexico',        group:'Group A',hS:0,aS:3,status:'FT',predH:1,predA:2,prob:[30,25,45],venue:'Estadio Azteca, Mexico City',         btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'Czechia 0-3 Mexico — Mexico perfect 9pts from 9. World beating form.' },
  { id:54, date:'2026-06-24',time:'02:00',home:'South Africa',  away:'South Korea',   group:'Group A',hS:1,aS:0,status:'FT',predH:0,predA:2,prob:[18,25,57],venue:'Estadio BBVA, Monterrey',             btts:{pred:'No',conf:60}, ou25:{pred:'Under',conf:55},reasoning:'MASSIVE UPSET — South Africa 1-0 South Korea. SA advance as best 3rd.' },
  // Jun 25
  { id:55, date:'2026-06-25',time:'21:00',home:'Curaçao',       away:'Ivory Coast',   group:'Group E',hS:null,aS:null,status:'NS',predH:0,predA:3,prob:[6,16,78], venue:'Lincoln Financial Field, Philadelphia',btts:{pred:'No',conf:80}, ou25:{pred:'Over',conf:78}, reasoning:'Ivory Coast 2-0 Curaçao — through to R32.' },
  { id:56, date:'2026-06-25',time:'21:00',home:'Ecuador',       away:'Germany',       group:'Group E',hS:null,aS:null,status:'NS',predH:0,predA:3,prob:[15,18,67],venue:'MetLife Stadium, East Rutherford NJ', btts:{pred:'No',conf:72}, ou25:{pred:'Over',conf:80}, reasoning:'SHOCK — Ecuador 2-1 Germany! One of the biggest tournament upsets.' },
  { id:57, date:'2026-06-25',time:'03:00',home:'Türkiye',       away:'United States', group:'Group D',hS:null,aS:null,status:'NS',predH:1,predA:2,prob:[28,22,50],venue:'SoFi Stadium, Inglewood CA',          btts:{pred:'Yes',conf:60},ou25:{pred:'Over',conf:65}, reasoning:'USA scored 4 in MD1. Türkiye lost 0-2. USA strong favorites — both sides likely to score.' },
  { id:58, date:'2026-06-25',time:'03:00',home:'Paraguay',      away:'Australia',     group:'Group D',hS:null,aS:null,status:'NS',predH:0,predA:2,prob:[20,25,55],venue:"Levi's Stadium, Santa Clara",         btts:{pred:'No',conf:62}, ou25:{pred:'Under',conf:56},reasoning:'Australia won 2-0 in MD1 with clean sheet. Paraguay failed to score vs USA. Australia comfortable.' },
  // Jun 26
  { id:59, date:'2026-06-26',time:'20:00',home:'Norway',        away:'France',        group:'Group I',hS:null,aS:null,status:'NS',predH:1,predA:1,prob:[38,28,34],venue:'Gillette Stadium, Foxborough MA',     btts:{pred:'Yes',conf:65},ou25:{pred:'Over',conf:68}, reasoning:'Norway 4-1 Iraq vs France 3-1 Senegal — both in excellent form. Changed from France win to draw; Norway are no pushover.' },
  { id:60, date:'2026-06-26',time:'20:00',home:'Senegal',       away:'Iraq',          group:'Group I',hS:null,aS:null,status:'NS',predH:2,predA:0,prob:[68,18,14],venue:'BMO Field, Toronto',                  btts:{pred:'No',conf:65}, ou25:{pred:'Over',conf:62}, reasoning:'Senegal need a win to have any chance. Iraq conceded 4 to Norway — Senegal quality should show.' },
  { id:61, date:'2026-06-26',time:'01:00',home:'Cape Verde',    away:'Saudi Arabia',  group:'Group H',hS:null,aS:null,status:'NS',predH:1,predA:1,prob:[32,34,34],venue:'NRG Stadium, Houston',                btts:{pred:'Yes',conf:55},ou25:{pred:'Under',conf:56},reasoning:'Both drew in MD1 (Cape Verde 0-0, Saudi 1-1). Expect another tight game — draw likely.' },
  { id:62, date:'2026-06-26',time:'01:00',home:'Uruguay',       away:'Spain',         group:'Group H',hS:null,aS:null,status:'NS',predH:1,predA:1,prob:[35,30,35],venue:'Estadio Akron, Guadalajara',          btts:{pred:'Yes',conf:60},ou25:{pred:'Over',conf:58}, reasoning:'Spain drew 0-0 in MD1 and looked blunt — changed from Spain win to draw. Uruguay drew 1-1. Too close to call.' },
  { id:63, date:'2026-06-26',time:'04:00',home:'Egypt',         away:'Iran',          group:'Group G',hS:null,aS:null,status:'NS',predH:1,predA:1,prob:[35,32,33],venue:'Lumen Field, Seattle',                btts:{pred:'Yes',conf:58},ou25:{pred:'Under',conf:55},reasoning:'Egypt drew 1-1 vs Belgium, Iran drew 2-2 vs NZ — both evenly matched, a draw is most likely in this Group G decider.' },
  { id:64, date:'2026-06-26',time:'04:00',home:'New Zealand',   away:'Belgium',       group:'Group G',hS:null,aS:null,status:'NS',predH:0,predA:2,prob:[15,22,63],venue:'BC Place, Vancouver',                 btts:{pred:'No',conf:65}, ou25:{pred:'Under',conf:58},reasoning:'Belgium drew 1-1 but need a win to qualify. NZ showed character with 2-2 vs Iran — Belgium should edge it.' },
  // Jun 27
  { id:65, date:'2026-06-27',time:'22:00',home:'Panama',        away:'England',       group:'Group L',hS:null,aS:null,status:'NS',predH:0,predA:4,prob:[5,14,81], venue:'MetLife Stadium, East Rutherford NJ', btts:{pred:'No',conf:82}, ou25:{pred:'Over',conf:82}, reasoning:'England scored 4 vs Croatia — upgraded from 0-3 to 0-4. Panama 0 goals in tournament. England to run riot.' },
  { id:66, date:'2026-06-27',time:'22:00',home:'Croatia',       away:'Ghana',         group:'Group L',hS:null,aS:null,status:'NS',predH:2,predA:1,prob:[50,25,25],venue:'Lincoln Financial Field, Philadelphia',btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'Croatia need a win to survive. Ghana 1-0 MD1 shows solidity. Croatia have the quality — tight game.' },
  { id:67, date:'2026-06-27',time:'00:30',home:'Colombia',      away:'Portugal',      group:'Group K',hS:null,aS:null,status:'NS',predH:2,predA:1,prob:[42,22,36],venue:'Hard Rock Stadium, Miami FL',         btts:{pred:'Yes',conf:62},ou25:{pred:'Over',conf:65}, reasoning:'Changed from Portugal win to Colombia win. Colombia 3-1 in MD1 and leading Group K — Portugal showed fragility vs DR Congo.' },
  { id:68, date:'2026-06-27',time:'00:30',home:'DR Congo',      away:'Uzbekistan',    group:'Group K',hS:null,aS:null,status:'NS',predH:2,predA:0,prob:[58,22,20],venue:'Mercedes-Benz Stadium, Atlanta',      btts:{pred:'No',conf:62}, ou25:{pred:'Over',conf:58}, reasoning:'DR Congo held Portugal — showed they are no pushovers. Uzbekistan lost 1-3. DR Congo to win.' },
  { id:69, date:'2026-06-27',time:'03:00',home:'Jordan',        away:'Argentina',     group:'Group J',hS:null,aS:null,status:'NS',predH:0,predA:4,prob:[5,12,83], venue:'AT&T Stadium, Arlington TX',          btts:{pred:'No',conf:82}, ou25:{pred:'Over',conf:82}, reasoning:'Argentina scored 3 and conceded 0 in MD1 — upgraded from 0-3 to 0-4. Jordan lost 1-3. Argentina will win heavily.' },
  { id:70, date:'2026-06-27',time:'03:00',home:'Algeria',       away:'Austria',       group:'Group J',hS:null,aS:null,status:'NS',predH:1,predA:2,prob:[30,25,45],venue:'Arrowhead Stadium, Kansas City MO',   btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'Algeria lost 0-3 vs Argentina. Austria won 3-1 vs Jordan. Austria have quality — Algeria will need to improve.' },

  // ── Jun 26-27 MD3 results ─────────────────────────────────────────────────
  { id:71, date:'2026-06-26',time:'19:30',home:'Türkiye',       away:'United States', group:'Group D',hS:3,aS:2,status:'FT',predH:1,predA:2,prob:[28,22,50],venue:'SoFi Stadium, Inglewood CA',          btts:{pred:'Yes',conf:60},ou25:{pred:'Over',conf:65}, reasoning:'SHOCK — Turkey 3-2 USA! Turkey eliminated but beat the group winners.' },
  { id:72, date:'2026-06-26',time:'19:30',home:'Paraguay',      away:'Australia',     group:'Group D',hS:0,aS:0,status:'FT',predH:1,predA:1,prob:[30,32,38],venue:"Levi's Stadium, Santa Clara",         btts:{pred:'Yes',conf:58},ou25:{pred:'Under',conf:54}, reasoning:'Paraguay 0-0 Australia — both advance. Australia qualify 2nd on GD.' },
  { id:73, date:'2026-06-26',time:'19:00',home:'Norway',        away:'France',        group:'Group I',hS:1,aS:4,status:'FT',predH:1,predA:1,prob:[38,28,34],venue:'Gillette Stadium, Foxborough MA',     btts:{pred:'Yes',conf:65},ou25:{pred:'Over',conf:68}, reasoning:'France 4-1 Norway — France win Group I with 9 points from 3 wins.' },
  { id:74, date:'2026-06-26',time:'19:00',home:'Senegal',       away:'Iraq',          group:'Group I',hS:5,aS:0,status:'FT',predH:2,predA:0,prob:[68,18,14],venue:'BMO Field, Toronto',                  btts:{pred:'No',conf:65}, ou25:{pred:'Over',conf:62}, reasoning:'Senegal 5-0 Iraq — brilliant exit, too late to qualify.' },
  { id:75, date:'2026-06-27',time:'01:00',home:'Cape Verde',    away:'Saudi Arabia',  group:'Group H',hS:0,aS:0,status:'FT',predH:1,predA:1,prob:[32,34,34],venue:'NRG Stadium, Houston',                btts:{pred:'Yes',conf:55},ou25:{pred:'Under',conf:56}, reasoning:'0-0 — Cape Verde finish 2nd with 3pts from 3 draws. Tournament fairytale.' },
  { id:76, date:'2026-06-27',time:'01:00',home:'Uruguay',       away:'Spain',         group:'Group H',hS:0,aS:1,status:'FT',predH:1,predA:1,prob:[35,30,35],venue:'Estadio Akron, Guadalajara',          btts:{pred:'Yes',conf:60},ou25:{pred:'Over',conf:58}, reasoning:'Spain 1-0 Uruguay — win Group H with 7 points.' },
  { id:77, date:'2026-06-27',time:'04:00',home:'New Zealand',   away:'Belgium',       group:'Group G',hS:1,aS:5,status:'FT',predH:0,predA:2,prob:[15,22,63],venue:'BC Place, Vancouver',                 btts:{pred:'No',conf:65}, ou25:{pred:'Under',conf:58}, reasoning:'Belgium 5-1 NZ — finally clicked. Win Group G on GD over Egypt.' },
  { id:78, date:'2026-06-27',time:'04:00',home:'Egypt',         away:'Iran',          group:'Group G',hS:1,aS:1,status:'FT',predH:1,predA:1,prob:[35,32,33],venue:'Lumen Field, Seattle',                btts:{pred:'Yes',conf:58},ou25:{pred:'Under',conf:55}, reasoning:'Egypt 1-1 Iran — Egypt finish 1st on GD. Both have draws and wins.' },
  { id:79, date:'2026-06-27',time:'22:00',home:'Panama',        away:'England',       group:'Group L',hS:0,aS:2,status:'FT',predH:0,predA:4,prob:[5,14,81], venue:'MetLife Stadium, East Rutherford NJ', btts:{pred:'No',conf:78}, ou25:{pred:'Over',conf:78}, reasoning:'England 2-0 Panama — comfortable win. 7pts from group.' },
  { id:80, date:'2026-06-27',time:'22:00',home:'Croatia',       away:'Ghana',         group:'Group L',hS:2,aS:1,status:'FT',predH:2,predA:1,prob:[50,25,25],venue:'Lincoln Financial Field, Philadelphia',btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'Croatia 2-1 Ghana — Croatia through. Ghana advance as best 3rd.' },
  { id:81, date:'2026-06-27',time:'18:30',home:'Colombia',      away:'Portugal',      group:'Group K',hS:0,aS:0,status:'FT',predH:2,predA:1,prob:[42,22,36],venue:'Hard Rock Stadium, Miami FL',         btts:{pred:'Yes',conf:62},ou25:{pred:'Over',conf:65}, reasoning:'0-0 draw — Colombia win Group K. Portugal advance as runners-up.' },
  { id:82, date:'2026-06-27',time:'22:30',home:'DR Congo',      away:'Uzbekistan',    group:'Group K',hS:3,aS:1,status:'FT',predH:2,predA:0,prob:[58,22,20],venue:'Mercedes-Benz Stadium, Atlanta',      btts:{pred:'No',conf:62}, ou25:{pred:'Over',conf:58}, reasoning:'DR Congo 3-1 Uzbekistan — advance as one of the best 3rd place teams.' },
  { id:83, date:'2026-06-27',time:'03:00',home:'Jordan',        away:'Argentina',     group:'Group J',hS:1,aS:3,status:'FT',predH:0,predA:4,prob:[5,12,83], venue:'AT&T Stadium, Arlington TX',          btts:{pred:'No',conf:78}, ou25:{pred:'Over',conf:78}, reasoning:'Argentina 3-1 Jordan — perfect 9pts, 8 goals, 1 conceded.' },
  { id:84, date:'2026-06-27',time:'03:00',home:'Algeria',       away:'Austria',       group:'Group J',hS:3,aS:3,status:'FT',predH:1,predA:2,prob:[30,25,45],venue:'Arrowhead Stadium, Kansas City MO',   btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'3-3 thriller! Austria advance 2nd on GD over Algeria.' },
  // ── ROUND OF 32 ──────────────────────────────────────────────────────────
  { id:90, date:'2026-06-28',time:'15:30',home:'South Africa',       away:'Canada',        group:'R32 · Match 73',hS:0,aS:1,status:'FT',predH:1,predA:2,prob:[32,25,43],venue:'SoFi Stadium, Inglewood CA',          btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'Canada 0-1 South Africa (Eustáquio 92\') — correct winner predicted. Canada into R16.' },
  { id:91, date:'2026-06-29',time:'13:30',home:'Brazil',       away:'Japan',        group:'R32 · Match 76',hS:2,aS:1,status:'FT',predH:3,predA:1,prob:[70,18,12],venue:'NRG Stadium, Houston',          btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'Brazil 2-1 Japan (Casemiro, Martinelli 90+5\') — correct winner, close on scoreline.' },
  { id:92, date:'2026-06-29',time:'17:00',home:'Germany',       away:'Paraguay',        group:'R32 · Match 74',hS:1,aS:1,status:'FT',predH:2,predA:0,prob:[72,18,10],venue:'Gillette Stadium, Foxborough MA',          btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'UPSET — 1-1 AET, Paraguay win 4-3 on penalties. Germany the first big shock exit.' },
  { id:93, date:'2026-06-29',time:'21:30',home:'Netherlands',       away:'Morocco',        group:'R32 · Match 75',hS:1,aS:1,status:'FT',predH:2,predA:1,prob:[58,22,20],venue:'AT&T Stadium, Arlington TX',          btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'UPSET — 1-1 AET, Morocco win 3-2 on penalties. Netherlands eliminated.' },
  { id:94, date:'2026-06-30',time:'13:30',home:'Ivory Coast',       away:'Norway',        group:'R32 · Match 78',hS:1,aS:2,status:'FT',predH:1,predA:2,prob:[32,25,43],venue:'BC Place, Vancouver',          btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'Norway 1-2 — correct prediction. Haaland scored, Antonio Nusa ×2 for Norway. Ivory Coast eliminated.' },
  { id:95, date:'2026-06-30',time:'17:30',home:'France',       away:'Sweden',        group:'R32 · Match 77',hS:3,aS:0,status:'FT',predH:2,predA:0,prob:[72,18,10],venue:'MetLife Stadium, East Rutherford NJ',          btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'France 3-0 Sweden — dominant. Mbappé brace (45\', 74\') + Barcola (53\'). Mbappé now on 6 tournament goals, joint Golden Boot leader with Messi.' },
  { id:96, date:'2026-06-30',time:'21:30',home:'Mexico',       away:'Ecuador',        group:'R32 · Match 79',hS:2,aS:0,status:'FT',predH:2,predA:1,prob:[55,22,23],venue:'Estadio Azteca, Mexico City',          btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'Mexico 2-0 Ecuador — Quiñones (22\') and Jiménez (31\'). Mexico march into R16.' },
  { id:97, date:'2026-07-01',time:'12:30',home:'England',       away:'DR Congo',        group:'R32 · Match 80',hS:null,aS:null,status:'NS',predH:3,predA:0,prob:[78,14,8],venue:'Lumen Field, Seattle',          btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'England 7pts, scored 6. DR Congo drew vs Portugal — quality gap should show.' },
  { id:98, date:'2026-07-01',time:'16:30',home:'Belgium',       away:'Senegal',        group:'R32 · Match 82',hS:null,aS:null,status:'NS',predH:2,predA:1,prob:[58,22,20],venue:'BMO Field, Toronto',          btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'Belgium 5-1 NZ in MD3 shows they clicked. Senegal 5-0 Iraq exit. Belgium to edge it.' },
  { id:99, date:'2026-07-01',time:'20:30',home:'United States',       away:'Bosnia & Herz.',        group:'R32 · Match 81',hS:null,aS:null,status:'NS',predH:2,predA:0,prob:[65,20,15],venue:'Rose Bowl, Pasadena CA',          btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'USA still group winners despite Turkey loss. Bosnia 4pts — USA at home should win.' },
  { id:100, date:'2026-07-02',time:'15:30',home:'Spain',       away:'Austria',        group:'R32 · Match 84',hS:null,aS:null,status:'NS',predH:2,predA:0,prob:[68,20,12],venue:'Hard Rock Stadium, Miami FL',          btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'Spain 7pts, 4-0 Saudi Arabia. Austria drew 3-3 Algeria — leaky defence. Spain to win.' },
  { id:101, date:'2026-07-02',time:'19:30',home:'Portugal',       away:'Croatia',        group:'R32 · Match 83',hS:null,aS:null,status:'NS',predH:2,predA:1,prob:[58,22,20],venue:'AT&T Stadium, Arlington TX',          btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'Portugal 5pts, 5-0 Uzbekistan shows firepower. Croatia beat Ghana to survive. Goals expected.' },
  { id:102, date:'2026-07-02',time:'23:30',home:'Switzerland',       away:'Algeria',        group:'R32 · Match 85',hS:null,aS:null,status:'NS',predH:2,predA:1,prob:[60,22,18],venue:'BC Place, Vancouver',          btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'Switzerland 7pts, clinical throughout. Algeria drew 3-3 Austria — can score but concede.' },
  { id:103, date:'2026-07-03',time:'14:30',home:'Australia',       away:'Egypt',        group:'R32 · Match 88',hS:null,aS:null,status:'NS',predH:1,predA:1,prob:[35,30,35],venue:'NRG Stadium, Houston',          btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'Australia 4pts, Egypt Group G winners. Well-matched — expect a tight knockout game.' },
  { id:104, date:'2026-07-03',time:'18:30',home:'Argentina',       away:'Cape Verde',        group:'R32 · Match 86',hS:null,aS:null,status:'NS',predH:4,predA:0,prob:[88,9,3],venue:'MetLife Stadium, East Rutherford NJ',          btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'Argentina perfect 9pts, 8 goals. Cape Verde drew all 3 to qualify. Argentina in a different class.' },
  { id:105, date:'2026-07-03',time:'22:00',home:'Colombia',       away:'Ghana',        group:'R32 · Match 87',hS:null,aS:null,status:'NS',predH:2,predA:1,prob:[60,22,18],venue:'Estadio Akron, Guadalajara',          btts:{pred:'Yes',conf:58},ou25:{pred:'Over',conf:60}, reasoning:'Colombia 7pts through Group K. Ghana 4pts as best 3rd — Colombia favourites.' },
]

export { DEMO_FIXTURES }

export function FixtureCard({ f, detailed }) {
  const hFlag = FLAGS[f.home] || '🏳'
  const aFlag = FLAGS[f.away] || '🏳'
  const isLive = f.status === 'LIVE'
  const isFin = f.status === 'FT'
  const hasScore = f.hS !== null && f.aS !== null

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10, padding: '12px 0',
      borderBottom: '1px solid var(--border2)'
    }}>
      {/* Time / Status */}
      <div style={{ minWidth: 60, textAlign: 'center' }}>
        {isLive
          ? <span style={{ color: 'var(--red)', fontWeight: 700, fontSize: 12 }}>🔴 LIVE</span>
          : isFin
            ? <span style={{ color: 'var(--accent)', fontSize: 11, fontWeight: 700 }}>FT</span>
            : <span style={{ color: 'var(--muted)', fontSize: 12 }}>{f.time}</span>
        }
        <div style={{ color: 'var(--muted)', fontSize: 10, marginTop: 2 }}>{f.date?.slice(5)}</div>
      </div>

      {/* Match */}
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'space-between' }}>
          <span style={{ fontWeight: hasScore && f.hS > f.aS ? 700 : 400 }}>
            {hFlag} {f.home}
          </span>
          <span style={{ fontWeight: 900, fontSize: 18, color: hasScore ? 'var(--accent)' : 'var(--muted)', minWidth: 60, textAlign: 'center' }}>
            {hasScore ? `${f.hS} – ${f.aS}` : 'vs'}
          </span>
          <span style={{ fontWeight: hasScore && f.aS > f.hS ? 700 : 400 }}>
            {f.away} {aFlag}
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4, flexWrap: 'wrap', gap: 4 }}>
          <span style={{ color: 'var(--muted)', fontSize: 11, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '55vw' }}>{f.group} · {f.venue}</span>
          {!hasScore && (
            <span style={{ color: '#7dd3fc', fontSize: 11 }}>
              🤖 Pred: {f.predH}–{f.predA} · W/D/L: {f.prob[0]}%/{f.prob[1]}%/{f.prob[2]}%
            </span>
          )}
        </div>
        {detailed && !hasScore && f.btts && f.ou25 && (
          <>
            <div style={{ display: 'flex', gap: 16, marginTop: 8, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 11, color: 'var(--muted)' }}>
                BTTS: <strong style={{ color: 'var(--gold)' }}>{f.btts.pred}</strong> ({f.btts.conf}%)
              </span>
              <span style={{ fontSize: 11, color: 'var(--muted)' }}>
                O/U 2.5: <strong style={{ color: 'var(--gold)' }}>{f.ou25.pred}</strong> ({f.ou25.conf}%)
              </span>
            </div>
            {f.reasoning && (
              <div style={{ fontSize: 12, color: 'var(--text2, #cbd5e1)', marginTop: 6, lineHeight: 1.4 }}>
                💡 {f.reasoning}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default function Fixtures({ liveFixtures }) {
  const [groupFilter, setGroupFilter] = useState('R32')
  const [roundFilter, setRoundFilter] = useState('all')

  const fixtures = liveFixtures?.length ? liveFixtures : DEMO_FIXTURES

  const groups = ['all', 'R32', 'Group A', 'Group B', 'Group C', 'Group D', 'Group E', 'Group F',
    'Group G', 'Group H', 'Group I', 'Group J', 'Group K', 'Group L']

  const isR32 = f => (f.group || '').includes('R32') || (f.group || '').includes('Round of 32')

  const filtered = fixtures.filter(f => {
    if (groupFilter === 'R32' && !isR32(f)) return false
    if (groupFilter !== 'all' && groupFilter !== 'R32' && f.group !== groupFilter) return false
    if (roundFilter === 'live' && f.status !== 'LIVE') return false
    if (roundFilter === 'upcoming' && f.status !== 'NS') return false
    if (roundFilter === 'finished' && f.status !== 'FT') return false
    return true
  })

  const byDate = filtered.reduce((acc, f) => {
    const d = f.date || 'TBC'
    if (!acc[d]) acc[d] = []
    acc[d].push(f)
    return acc
  }, {})

  // R32 quick predictions grid
  const r32Fixtures = fixtures.filter(isR32)
  const r32Upcoming = r32Fixtures.filter(f => f.status === 'NS')
  const r32Done     = r32Fixtures.filter(f => f.status === 'FT')

  return (
    <div className="page-content">
      <div className="section-title">📅 Fixtures & Results</div>

      {/* R32 Predictions Banner */}
      {groupFilter === 'R32' && (
        <div style={{ background: 'linear-gradient(135deg,rgba(30,64,175,0.2),rgba(109,40,217,0.15))', border: '1px solid rgba(147,197,253,0.25)', borderRadius: 12, padding: '14px 16px', marginBottom: 16 }}>
          <div style={{ fontSize: 13, fontWeight: 800, color: '#93c5fd', marginBottom: 10 }}>
            🤖 Round of 32 — BetBud Score Predictions
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(280px,1fr))', gap: 8 }}>
            {r32Fixtures.map(f => {
              const hFlag = FLAGS[f.home] || '🏳'
              const aFlag = FLAGS[f.away] || '🏳'
              const done = f.status === 'FT' && f.hS !== null
              const correct = done && f.hS === f.predH && f.aS === f.predA
              const dirCorrect = done && ((f.hS > f.aS) === (f.predH > f.predA) || (f.hS === f.aS) === (f.predH === f.predA))
              return (
                <div key={f.id} style={{
                  background: done ? (correct ? 'rgba(74,222,128,0.08)' : dirCorrect ? 'rgba(251,191,36,0.08)' : 'rgba(255,255,255,0.04)') : 'rgba(255,255,255,0.04)',
                  border: `1px solid ${done ? (correct ? 'rgba(74,222,128,0.3)' : dirCorrect ? 'rgba(251,191,36,0.3)' : 'rgba(255,255,255,0.1)') : 'rgba(255,255,255,0.1)'}`,
                  borderRadius: 8, padding: '8px 10px',
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8
                }}>
                  <div style={{ fontSize: 12, flex: 1, minWidth: 0 }}>
                    <span style={{ marginRight: 4 }}>{hFlag}</span>
                    <span style={{ fontWeight: 600, fontSize: 11 }}>{f.home.split(' ')[0]}</span>
                  </div>
                  <div style={{ textAlign: 'center', flexShrink: 0 }}>
                    {done ? (
                      <div style={{ fontSize: 11 }}>
                        <span style={{ color: '#94a3b8', fontSize: 10 }}>Pred </span>
                        <span style={{ fontWeight: 700, color: '#7dd3fc' }}>{f.predH}–{f.predA}</span>
                        <span style={{ color: '#94a3b8', fontSize: 10 }}> · Act </span>
                        <span style={{ fontWeight: 700, color: correct ? '#4ade80' : '#f87171' }}>{f.hS}–{f.aS}</span>
                        <span style={{ marginLeft: 4 }}>{correct ? '✅' : dirCorrect ? '↗️' : '❌'}</span>
                      </div>
                    ) : (
                      <div style={{ fontWeight: 800, fontSize: 15, color: '#fbbf24' }}>
                        {f.predH}–{f.predA}
                      </div>
                    )}
                    <div style={{ fontSize: 10, color: '#64748b', marginTop: 1 }}>{f.time} GMT</div>
                  </div>
                  <div style={{ fontSize: 12, flex: 1, textAlign: 'right', minWidth: 0 }}>
                    <span style={{ fontWeight: 600, fontSize: 11 }}>{f.away.split(' ')[0]}</span>
                    <span style={{ marginLeft: 4 }}>{aFlag}</span>
                  </div>
                </div>
              )
            })}
          </div>
          <div style={{ fontSize: 11, color: '#64748b', marginTop: 10 }}>
            {r32Done.length}/16 played · {r32Upcoming.length} remaining · Times in GMT
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        <select className="select" value={groupFilter} onChange={e => setGroupFilter(e.target.value)}>
          {groups.map(g => (
            <option key={g} value={g}>
              {g === 'all' ? 'All Fixtures' : g === 'R32' ? '⚔️ Round of 32' : g}
            </option>
          ))}
        </select>
        <select className="select" value={roundFilter} onChange={e => setRoundFilter(e.target.value)}>
          <option value="all">All Status</option>
          <option value="upcoming">Upcoming</option>
          <option value="finished">Finished</option>
        </select>
        <div style={{ fontSize: 12, color: 'var(--muted)', display: 'flex', alignItems: 'center' }}>
          {filtered.length} match{filtered.length !== 1 ? 'es' : ''}
        </div>
      </div>

      <div className="card">
        {Object.keys(byDate).sort().map(date => (
          <div key={date}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--gold)', padding: '8px 0 4px', textTransform: 'uppercase', letterSpacing: 1 }}>
              📆 {date}
            </div>
            {byDate[date].map(f => <FixtureCard key={f.id} f={f} detailed />)}
          </div>
        ))}
        {filtered.length === 0 && (
          <div style={{ textAlign: 'center', padding: 32, color: 'var(--muted)' }}>No fixtures match filter</div>
        )}
      </div>
    </div>
  )
}
