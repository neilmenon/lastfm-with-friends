import { tassign } from "tassign";
import { SETTINGS_MODEL, USER_MODEL } from "./actions";
import { SettingsModel } from "./models/settingsModel";
import { UserModel } from "./models/userGroupModel";

export interface AppState {
    userModel: UserModel
    settingsModel: SettingsModel
}

export const INITIAL_STATE: AppState = {
    userModel: null,
    settingsModel: null
}

function userModel(state: AppState, action) {
    var newState = state
    newState.userModel = action.userModel
    return tassign(state, newState)
}

function settingsModel(state: AppState, action) {
    var newState = state
    newState.settingsModel = action.settingsModel
    return tassign(state, newState)
}

export function appReducer(state: AppState = INITIAL_STATE, action): AppState {
    switch (action.type) {
        case USER_MODEL: return userModel(state, action)
        case SETTINGS_MODEL: return settingsModel(state, action)
    }
    return state
}

export const rootReducer = appReducer