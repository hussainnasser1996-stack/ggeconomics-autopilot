import React from "react";
import { CalculateMetadataFunction, staticFile } from "remotion";
import { NewsShort, ShortSpec, shortFrames } from "./NewsShort";

/** Generic daily Short: the whole episode comes in as JSON props (no code edit per episode).
 *  render: npx remotion render src/index.ts DailyShort out.mp4 --props=../autopilot/queue/<date>/spec.json
 *  spec.timelinePath points at public/vo/<id>/timeline.json; it's fetched at metadata time. */
export type DailyProps = { spec: ShortSpec & { timelinePath?: string } };

export const dailyMetadata: CalculateMetadataFunction<DailyProps> = async ({ props }) => {
  const spec = { ...props.spec };
  if (spec.timelinePath) {
    const res = await fetch(staticFile(spec.timelinePath));
    spec.timeline = await res.json();
  }
  return { durationInFrames: shortFrames(spec as ShortSpec), props: { spec } };
};

export const DailyShort: React.FC<DailyProps> = ({ spec }) => <NewsShort spec={spec as ShortSpec} />;
