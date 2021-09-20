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