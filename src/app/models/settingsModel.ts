import { discreteTimePeriods } from "../constants"

export class SettingsModel {
    showUpdateInterval: boolean
    chartReleaseType: string
    chartTimePeriodDays: number
    leaderboardTimePeriodDays: number
    groupExpandedList: any
    trendMode: string
    chartUser: string

    constructor() {
        this.showUpdateInterval = false
        this.chartReleaseType = "random"
        this.chartTimePeriodDays = 30
        this.leaderboardTimePeriodDays = 7
        this.groupExpandedList = {}
        this.trendMode = "leaderboard-cu"
        this.chartUser = "everyone"
    }
}

export function getSettingsModel(raw: any): SettingsModel {
    if (!raw) { return new SettingsModel() }

    let s: SettingsModel = new SettingsModel(), local: any
    if (typeof(raw) == "string") {
        local = JSON.parse(raw)
    } else if (typeof(raw) == "object") {
        local = raw
    } else { return new SettingsModel() }

    for (const key of Object.keys(s)) {
        if (local[key] === undefined) {
            local[key] = s[key]
        }
    }

    return local
}