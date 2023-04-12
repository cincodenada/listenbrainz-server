/** Main entities */
declare type MusicBrainzArtist = {
  name: string;
  join_phrase: string;
  area: string;
  begin_year: number;
  rels: { [key: string]: string };
  //   rels: Record<string, string>;
  type: string;
};

declare type MusicBrainzArtistCredit = {
  name: string;
  joinphrase: string;
  artist: {
    name: string;
    "sort-name": string;
    id: string;
    disambiguation: string;
    type: string | null;
    "type-id": string;
  };
};

declare type MusicBrainzReleaseGroup = {
  title: string;
  id: string;
  disambiguation: string;
  "first-release-date": string;
  "primary-type": string;
  "primary-type-id": string;
  "secondary-types": string[];
  "secondary-type-ids": string[];
};

declare type MusicBrainzTrack = {
  number: string;
  length: number;
  position: number;
  title: string;
  id: string;
  recording: MusicBrainzRecording;
};
declare type MusicBrainzMedia = {
  title: string;
  position: number;
  tracks: Array<MusicBrainzTrack>;
  format: string;
  "format-id": string;
  "track-offset": number;
  "track-count": number;
};
declare type MusicBrainzRelease = {
  title: string;
  id: string;
  packaging: string;
  "packaging-id": string;
  date: string;
  status: string;
  barcode: string | number;
  "status-id": string;
  disambiguation: string;
  quality: string;
  country: string;
};
declare type MusicBrainzReleaseWithMedia = MusicBrainzRelease & {
  media: Array<MusicBrainzMedia>;
};
// With ?inc=release-groups
declare type MusicBrainzReleaseWithReleaseGroup = MusicBrainzRelease & {
  "release-group": MusicBrainzReleaseGroup;
};

declare type MusicBrainzRecording = {
  title: string;
  id: string;
  "first-release-date": string;
  length: number;
  video: boolean;
  disambiguation: string;
  "artist-credit": Array<MusicBrainzArtistCredit>;
};
// With ?inc=releases
declare type MusicBrainzRecordingWithReleases = MusicBrainzRecording & {
  releases: Array<MusicBrainzRelease>;
};

declare type MusicBrainzRecordingRel = {
  artist_mbid: string;
  artist_name: string;
  instrument?: string;
  type: string;
};

/** Tags / Genres / Moods */
declare type ArtistTag = {
  artist_mbid: string;
  count: number;
  genre_mbid?: string;
  tag: string;
};
declare type RecordingTag = {
  count: number;
  genre_mbid?: string;
  tag: string;
};

declare type ReleaseGroupTag = RecordingTag & {
  release_group_mbid: string;
};

declare type ListenMetadata = {
  artist?: {
    name?: string;
    artists?: Array<MusicBrainzArtist>;
  };
  recording?: {
    rels?: Array<MusicBrainzRecordingRel>;
    duration?: number;
  };
  release?: {
    caa_id: ?number;
    caa_release_mbid: ?string;
    mbid?: string;
    year?: number;
  };
  tag?: {
    artist?: Array<ArtistTag>;
    recording?: Array<RecordingTag>;
    release_group?: Array<ReleaseGroupTag>;
  };
};

declare type MetadataLookup = {
  metadata: ListenMetadata;
  artist_credit_name: string;
  artist_mbids: string[];
  recording_mbid: string;
  recording_name: string;
  release_mbid: string;
  release_name: string;
};
