import React from "react";
import { Composition } from "remotion";
import { Ident, IDENT_FRAMES } from "./Ident";
import { NewsShort, shortFrames } from "./news/NewsShort";
import { gtaShort } from "./episodes/gtaShort";
import { LongForm, longFrames } from "./news/LongForm";
import { gtaLong } from "./episodes/gtaLong";
import { Walkthrough, walkFrames } from "./walkthrough/Walkthrough";
import { Thumb } from "./news/Thumb";
import { eldenShort } from "./episodes/eldenShort";
import { CarouselSlide } from "./news/Carousel";
import { gtaCarousel } from "./episodes/gtaCarousel";
import { DailyShort, dailyMetadata } from "./news/Daily";
import { TopFive, topMetadata } from "./news/TopFive";
import topFivePilot from "./episodes/topFivePilot.json";
import { TopRanking, rankMetadata } from "./news/TopRanking";
import { LongTop, longMetadata } from "./news/LongTop";
import longTop10 from "./episodes/longTop10.json";
import longTop10Text from "./episodes/longTop10_text.json";
import longTop10Voice from "./episodes/longTop10_voice.json";
import topTenRanking from "./episodes/topTenRanking.json";
import { Avatar, Banner, BannerSafe } from "./BrandAssets";
import { eldenWalk } from "./episodes/eldenWalk";
import { HoldScreen, Stinger, LiveOverlay, LOOP } from "./twitch/TwitchKit";

export const Root: React.FC = () => (
  <>
    <Composition id="Ident" component={Ident} durationInFrames={IDENT_FRAMES} fps={30} width={1920} height={1080} />
    <Composition id="Ident9x16" component={Ident} durationInFrames={IDENT_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="TopFive" component={TopFive} calculateMetadata={topMetadata} durationInFrames={560} fps={30} width={1080} height={1920} defaultProps={topFivePilot as any} />
    <Composition id="LongTop" component={LongTop} calculateMetadata={longMetadata} durationInFrames={9000} fps={30} width={1920} height={1080} defaultProps={{ spec: longTop10 } as any} />
    <Composition id="LongTopText" component={LongTop} calculateMetadata={longMetadata} durationInFrames={9000} fps={30} width={1920} height={1080} defaultProps={{ spec: longTop10Text } as any} />
    <Composition id="LongTopVoice" component={LongTop} calculateMetadata={longMetadata} durationInFrames={9000} fps={30} width={1920} height={1080} defaultProps={{ spec: longTop10Voice } as any} />
    <Composition id="TopRanking" component={TopRanking} calculateMetadata={rankMetadata} durationInFrames={2200} fps={30} width={1080} height={1920} defaultProps={topTenRanking as any} />
    <Composition id="GtaShort" component={NewsShort} durationInFrames={shortFrames(gtaShort)} fps={30} width={1080} height={1920} defaultProps={{ spec: gtaShort }} />
    <Composition id="GtaFeed4x5" component={NewsShort} durationInFrames={shortFrames(gtaShort)} fps={30} width={1080} height={1350} defaultProps={{ spec: gtaShort }} />
    <Composition id="GtaLong" component={LongForm} durationInFrames={longFrames(gtaLong)} fps={30} width={1920} height={1080} defaultProps={{ spec: gtaLong }} />
    <Composition id="TwitchStartingSoon" component={HoldScreen} durationInFrames={LOOP} fps={30} width={1920} height={1080} defaultProps={{ title: "STARTING SOON", sub: "LOADING SAVE FILE", period: LOOP / 4 }} />
    <Composition id="TwitchBRB" component={HoldScreen} durationInFrames={LOOP} fps={30} width={1920} height={1080} defaultProps={{ title: "BE RIGHT BACK", sub: "AUTOSAVING", period: LOOP / 4 }} />
    <Composition id="TwitchStinger" component={Stinger} durationInFrames={36} fps={30} width={1920} height={1080} />
    <Composition id="TwitchOverlay" component={LiveOverlay} durationInFrames={LOOP} fps={30} width={1920} height={1080} defaultProps={{ game: "ELDEN RING" }} />
    <Composition id="TwitchOverlayDemo" component={LiveOverlay} durationInFrames={450} fps={30} width={1920} height={1080} defaultProps={{ game: "ELDEN RING", demoSrc: "v3", demoFrom: 690 }} />
    <Composition id="EldenWalk" component={Walkthrough} durationInFrames={walkFrames(eldenWalk)} fps={30} width={1920} height={1080} defaultProps={{ spec: eldenWalk }} />
    <Composition id="ThumbGta" component={Thumb} durationInFrames={1} fps={30} width={1280} height={720} defaultProps={{ src: "v2", at: 290.6, big: "$1B", line1: "BEFORE IT'S\nEVEN OUT", tag: "GTA VI" }} />
    <Composition id="ThumbElden" component={Thumb} durationInFrames={1} fps={30} width={1280} height={720} defaultProps={{ src: "v3", at: 678, big: "PT.1", line1: "CHAPEL TO\nLIMGRAVE", tag: "ELDEN RING" }} />
    <Composition id="EldenShort" component={NewsShort} durationInFrames={shortFrames(eldenShort)} fps={30} width={1080} height={1920} defaultProps={{ spec: eldenShort }} />
    <Composition id="GtaCarousel1" component={CarouselSlide} durationInFrames={1} fps={30} width={1080} height={1350} defaultProps={{ slides: gtaCarousel, i: 0, credit: "GAMEPLAY: ROCKSTAR GAMES" }} />
    <Composition id="GtaCarousel2" component={CarouselSlide} durationInFrames={1} fps={30} width={1080} height={1350} defaultProps={{ slides: gtaCarousel, i: 1, credit: "GAMEPLAY: ROCKSTAR GAMES" }} />
    <Composition id="GtaCarousel3" component={CarouselSlide} durationInFrames={1} fps={30} width={1080} height={1350} defaultProps={{ slides: gtaCarousel, i: 2, credit: "GAMEPLAY: ROCKSTAR GAMES" }} />
    <Composition id="GtaCarousel4" component={CarouselSlide} durationInFrames={1} fps={30} width={1080} height={1350} defaultProps={{ slides: gtaCarousel, i: 3, credit: "GAMEPLAY: ROCKSTAR GAMES" }} />
    <Composition id="GtaCarousel5" component={CarouselSlide} durationInFrames={1} fps={30} width={1080} height={1350} defaultProps={{ slides: gtaCarousel, i: 4, credit: "GAMEPLAY: ROCKSTAR GAMES" }} />
    <Composition id="DailyShort" component={DailyShort} calculateMetadata={dailyMetadata} durationInFrames={300} fps={30} width={1080} height={1920}
      defaultProps={{ spec: { tag: "", topic: "", vo: "", timeline: { duration: 1, lines: [], words: [] }, clips: [], cards: [], credit: "", endLine: "", noBed: true } as any }} />
    <Composition id="DailyFeed4x5" component={DailyShort} calculateMetadata={dailyMetadata} durationInFrames={300} fps={30} width={1080} height={1350}
      defaultProps={{ spec: { tag: "", topic: "", vo: "", timeline: { duration: 1, lines: [], words: [] }, clips: [], cards: [], credit: "", endLine: "", noBed: true } as any }} />
    <Composition id="DailyCarousel" component={CarouselSlide} durationInFrames={1} fps={30} width={1080} height={1350}
      defaultProps={{ slides: gtaCarousel, i: 0, credit: "" }} />
    <Composition id="BrandAvatar" component={Avatar} durationInFrames={1} fps={30} width={800} height={800} />
    <Composition id="BrandBanner" component={Banner} durationInFrames={1} fps={30} width={2560} height={1440} />
    <Composition id="BrandBannerSafe" component={BannerSafe} durationInFrames={1} fps={30} width={2560} height={1440} />
  </>
);
