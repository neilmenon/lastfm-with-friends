import { SettingsModel } from "./settingsModel"

export class UserModel {
    display_name: string
    groups: Array<UserGroupModel>
    last_update: string
    profile_image: string
    progress: number
    registered: string
    scrobbles: number
    settings: SettingsModel
    user_id: number
    username: string
    group_session: GroupSessionModel
    stats: PersonalStatsModel
}

export class UserGroupModel {
    created: string
    description: string
    id: number
    join_code: string
    members: Array<MemberModel>
    name: string
    owner: string
}

export class MemberModel {
    id: number
    username: string
}

export class GroupDetailModel {
    created: string
    description: string
    id: number
    join_code: string
    users: Array<GroupDetailMemberModel>
    name: string
    owner: string
}

export class GroupDetailMemberModel {
    joined: string
    profile_image: string
    registered: string
    scrobbles: number
    user_id: number
    username: string
}

export class GroupSessionModel {
    created: string
    group_jc: string
    id: number
    is_silent: boolean
    members: Array<GroupSessionMemberModel>
    owner: string
}

export class GroupSessionMemberModel {
    username: string
    profile_image: string
}

export class PersonalStatsModel {
    cant_get_enough: { album: string, artist: string, artist_image: string, artist_url: string, image: string, scrobbles: number, track: string }
    date_generated: string
    most_active_hour: number
    scrobble_compare: { current: number, percent: number, previous: number }
    time_period_days: number
    top_genre: { genre_count: number, name: string, sum_scrobbles: 109 }
    top_rising: Array<{ artist: string, artist_id: number, percent: number, prev_scrobbles: number, scrobbles: number }>
    username: string
}