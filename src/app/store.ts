import { tassign } from "tassign";
import { UPDATE_USER_MODEL } from "./actions";
import { UserModel } from "./models/userGroupModel";

export interface AppState {
    userModel: UserModel
}

export const INITIAL_STATE: AppState = {
    userModel: null
}

function updateUserModel(state: AppState, action) {
    var newState = state
    newState.userModel = action.userModel
    return tassign(state, newState)
}

export function appReducer(state: AppState = INITIAL_STATE, action): AppState {
    switch (action.type) {
        case UPDATE_USER_MODEL: return updateUserModel(state, action)
    }
    return state
}