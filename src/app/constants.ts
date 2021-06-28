import { TimePeriodModel } from "./models/timePeriodModel"

export const discreteTimePeriods: Array<TimePeriodModel> = [
    {'label': '24 hours', 'days': 1},
    {'label': '7 days', 'days': 7},
    {'label': '14 days', 'days': 14},
    {'label': '30 days', 'days': 30},
    {'label': '60 days', 'days': 60},
    {'label': '90 days', 'days': 90},
    {'label': '180 days', 'days': 180},
    {'label': '365 days', 'days': 365},
    {'label': 'All time', 'days': -1}
]
export const releaseTypes: Array<string> = ['track', 'artist', 'album']