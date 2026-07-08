// FINAL group stage standings — verified from FIFA website 2026-06-28
export const GROUPS = {
  A: {
    teams: [
      { name: 'Mexico',       flag: '🇲🇽', p: 3, w: 3, d: 0, l: 0, gf: 6,  ga: 0,  pts: 9, rating: 7.8, form: 'WWW' },
      { name: 'South Africa', flag: '🇿🇦', p: 3, w: 1, d: 1, l: 1, gf: 2,  ga: 3,  pts: 4, rating: 6.2, form: 'LDW' },
      { name: 'South Korea',  flag: '🇰🇷', p: 3, w: 1, d: 0, l: 2, gf: 2,  ga: 3,  pts: 3, rating: 7.2, form: 'WLL' },
      { name: 'Czechia',      flag: '🇨🇿', p: 3, w: 0, d: 1, l: 2, gf: 2,  ga: 6,  pts: 1, rating: 6.8, form: 'LDL' },
    ],
    predWinner: 'Mexico', predRunner: 'South Africa',
  },
  B: {
    teams: [
      { name: 'Switzerland',   flag: '🇨🇭', p: 3, w: 2, d: 1, l: 0, gf: 5, ga: 3,  pts: 7, rating: 7.5, form: 'DWW' },
      { name: 'Canada',        flag: '🇨🇦', p: 3, w: 1, d: 1, l: 1, gf: 4, ga: 4,  pts: 4, rating: 7.4, form: 'DLW' },
      { name: 'Bosnia & Herz.',flag: '🇧🇦', p: 3, w: 1, d: 1, l: 1, gf: 5, ga: 4,  pts: 4, rating: 6.5, form: 'DWL' },
      { name: 'Qatar',         flag: '🇶🇦', p: 3, w: 0, d: 1, l: 2, gf: 2, ga: 5,  pts: 1, rating: 6.0, form: 'DLL' },
    ],
    predWinner: 'Switzerland', predRunner: 'Canada',
  },
  C: {
    teams: [
      { name: 'Brazil',   flag: '🇧🇷', p: 3, w: 2, d: 1, l: 0, gf: 7, ga: 1, pts: 7, rating: 8.7, form: 'DWW' },
      { name: 'Morocco',  flag: '🇲🇦', p: 3, w: 2, d: 1, l: 0, gf: 6, ga: 3, pts: 7, rating: 7.6, form: 'DWW' },
      { name: 'Scotland', flag: '🏴󠁧󠁢󠁳󠁣󠁴󠁿', p: 3, w: 1, d: 0, l: 2, gf: 1, ga: 4, pts: 3, rating: 6.8, form: 'WLL' },
      { name: 'Haiti',    flag: '🇭🇹', p: 3, w: 0, d: 0, l: 3, gf: 2, ga: 8, pts: 0, rating: 5.5, form: 'LLL' },
    ],
    predWinner: 'Brazil', predRunner: 'Morocco',
  },
  D: {
    teams: [
      { name: 'United States', flag: '🇺🇸', p: 3, w: 2, d: 0, l: 1, gf: 8, ga: 4, pts: 6, rating: 7.8, form: 'WWL' },
      { name: 'Australia',     flag: '🇦🇺', p: 3, w: 1, d: 1, l: 1, gf: 2, ga: 2, pts: 4, rating: 7.0, form: 'WLD' },
      { name: 'Paraguay',      flag: '🇵🇾', p: 3, w: 1, d: 1, l: 1, gf: 2, ga: 5, pts: 4, rating: 6.5, form: 'LWD' },
      { name: 'Türkiye',       flag: '🇹🇷', p: 3, w: 1, d: 0, l: 2, gf: 4, ga: 5, pts: 3, rating: 7.4, form: 'LLW' },
    ],
    predWinner: 'USA', predRunner: 'Australia',
  },
  E: {
    teams: [
      { name: 'Germany',     flag: '🇩🇪', p: 3, w: 2, d: 0, l: 1, gf: 10, ga: 4, pts: 6, rating: 8.5, form: 'WWL' },
      { name: 'Ivory Coast', flag: '🇨🇮', p: 3, w: 2, d: 0, l: 1, gf: 3,  ga: 2, pts: 6, rating: 7.0, form: 'WLW' },
      { name: 'Ecuador',     flag: '🇪🇨', p: 3, w: 1, d: 1, l: 1, gf: 2,  ga: 2, pts: 4, rating: 7.0, form: 'LDW' },
      { name: 'Curaçao',     flag: '🇨🇼', p: 3, w: 0, d: 1, l: 2, gf: 1,  ga: 8, pts: 1, rating: 5.5, form: 'LDL' },
    ],
    predWinner: 'Germany', predRunner: 'Ivory Coast',
  },
  F: {
    teams: [
      { name: 'Netherlands', flag: '🇳🇱', p: 3, w: 2, d: 1, l: 0, gf: 10, ga: 3, pts: 7, rating: 8.4, form: 'DWW' },
      { name: 'Japan',       flag: '🇯🇵', p: 3, w: 1, d: 2, l: 0, gf: 7,  ga: 3, pts: 5, rating: 7.6, form: 'DWD' },
      { name: 'Sweden',      flag: '🇸🇪', p: 3, w: 1, d: 1, l: 1, gf: 7,  ga: 7, pts: 4, rating: 7.0, form: 'WLD' },
      { name: 'Tunisia',     flag: '🇹🇳', p: 3, w: 0, d: 0, l: 3, gf: 2,  ga: 13,pts: 0, rating: 6.3, form: 'LLL' },
    ],
    predWinner: 'Netherlands', predRunner: 'Japan',
  },
  G: {
    teams: [
      { name: 'Egypt',       flag: '🇪🇬', p: 3, w: 1, d: 2, l: 0, gf: 5, ga: 3, pts: 5, rating: 7.0, form: 'DWD' },
      { name: 'Belgium',     flag: '🇧🇪', p: 3, w: 1, d: 2, l: 0, gf: 7, ga: 3, pts: 5, rating: 8.2, form: 'DDW' },
      { name: 'Iran',        flag: '🇮🇷', p: 3, w: 0, d: 3, l: 0, gf: 3, ga: 3, pts: 3, rating: 6.8, form: 'DDD' },
      { name: 'New Zealand', flag: '🇳🇿', p: 3, w: 0, d: 1, l: 2, gf: 4, ga: 9, pts: 1, rating: 5.8, form: 'DLL' },
    ],
    predWinner: 'Belgium', predRunner: 'Egypt', actualWinner: 'Egypt', actualRunner: 'Belgium', predWon: false,
  },
  H: {
    teams: [
      { name: 'Spain',        flag: '🇪🇸', p: 3, w: 2, d: 1, l: 0, gf: 5, ga: 1, pts: 7, rating: 9.0, form: 'DWW' },
      { name: 'Cape Verde',   flag: '🇨🇻', p: 3, w: 0, d: 3, l: 0, gf: 2, ga: 2, pts: 3, rating: 5.8, form: 'DDD' },
      { name: 'Uruguay',      flag: '🇺🇾', p: 3, w: 0, d: 2, l: 1, gf: 3, ga: 4, pts: 2, rating: 7.8, form: 'DDL' },
      { name: 'Saudi Arabia', flag: '🇸🇦', p: 3, w: 0, d: 2, l: 1, gf: 1, ga: 5, pts: 2, rating: 6.5, form: 'DLD' },
    ],
    predWinner: 'Spain', predRunner: 'Cape Verde',
  },
  I: {
    teams: [
      { name: 'France',  flag: '🇫🇷', p: 3, w: 3, d: 0, l: 0, gf: 10, ga: 2, pts: 9, rating: 9.2, form: 'WWW' },
      { name: 'Norway',  flag: '🇳🇴', p: 3, w: 2, d: 0, l: 1, gf: 8,  ga: 5, pts: 6, rating: 8.0, form: 'WWL' },
      { name: 'Senegal', flag: '🇸🇳', p: 3, w: 1, d: 0, l: 2, gf: 7,  ga: 7, pts: 3, rating: 7.4, form: 'LLW' },
      { name: 'Iraq',    flag: '🇮🇶', p: 3, w: 0, d: 0, l: 3, gf: 1,  ga: 12,pts: 0, rating: 5.8, form: 'LLL' },
    ],
    predWinner: 'France', predRunner: 'Norway',
  },
  J: {
    teams: [
      { name: 'Argentina', flag: '🇦🇷', p: 3, w: 3, d: 0, l: 0, gf: 8, ga: 1, pts: 9, rating: 9.1, form: 'WWW' },
      { name: 'Austria',   flag: '🇦🇹', p: 3, w: 1, d: 1, l: 1, gf: 7, ga: 5, pts: 4, rating: 7.5, form: 'WLD' },
      { name: 'Algeria',   flag: '🇩🇿', p: 3, w: 1, d: 1, l: 1, gf: 5, ga: 7, pts: 4, rating: 6.8, form: 'LWD' },
      { name: 'Jordan',    flag: '🇯🇴', p: 3, w: 0, d: 0, l: 3, gf: 2, ga: 9, pts: 0, rating: 5.6, form: 'LLL' },
    ],
    predWinner: 'Argentina', predRunner: 'Austria',
  },
  K: {
    teams: [
      { name: 'Colombia',  flag: '🇨🇴', p: 3, w: 2, d: 1, l: 0, gf: 4, ga: 1, pts: 7, rating: 8.0, form: 'WWD' },
      { name: 'Portugal',  flag: '🇵🇹', p: 3, w: 1, d: 2, l: 0, gf: 6, ga: 1, pts: 5, rating: 8.8, form: 'DWD' },
      { name: 'DR Congo',  flag: '🇨🇩', p: 3, w: 1, d: 1, l: 1, gf: 4, ga: 2, pts: 4, rating: 6.0, form: 'DLW' },
      { name: 'Uzbekistan',flag: '🇺🇿', p: 3, w: 0, d: 0, l: 3, gf: 1, ga: 11,pts: 0, rating: 6.2, form: 'LLL' },
    ],
    predWinner: 'Portugal', predRunner: 'Colombia', actualWinner: 'Colombia', actualRunner: 'Portugal', predWon: false,
  },
  L: {
    teams: [
      { name: 'England', flag: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', p: 3, w: 2, d: 1, l: 0, gf: 6, ga: 2, pts: 7, rating: 8.9, form: 'WDW' },
      { name: 'Croatia', flag: '🇭🇷', p: 3, w: 2, d: 0, l: 1, gf: 5, ga: 5, pts: 6, rating: 7.5, form: 'LWW' },
      { name: 'Ghana',   flag: '🇬🇭', p: 3, w: 1, d: 1, l: 1, gf: 2, ga: 2, pts: 4, rating: 6.5, form: 'WDL' },
      { name: 'Panama',  flag: '🇵🇦', p: 3, w: 0, d: 0, l: 3, gf: 0, ga: 4, pts: 0, rating: 5.8, form: 'LLL' },
    ],
    predWinner: 'England', predRunner: 'Croatia',
  },
}
