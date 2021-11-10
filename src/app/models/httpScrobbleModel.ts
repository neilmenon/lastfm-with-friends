export class HttpScrobbleModel {
    // the model for scrobbling tracks through the app
    artist: string
    track: string
    album: string
    timestamp: string

    constructor() {
        this.artist = null
        this.track = null
        this.album = null
        this.timestamp = null
    }
}