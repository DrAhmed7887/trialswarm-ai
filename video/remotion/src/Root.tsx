import React from 'react';
import { Composition } from 'remotion';
import { TrialSwarmPitch, TOTAL_FRAMES, FPS } from './TrialSwarmPitch';
import {
  TrialSwarmDemo,
  DEMO_TOTAL_FRAMES,
  DEMO_FPS,
} from './TrialSwarmDemo';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="TrialSwarmPitch"
        component={TrialSwarmPitch}
        durationInFrames={TOTAL_FRAMES}
        fps={FPS}
        width={1920}
        height={1080}
      />
      <Composition
        id="TrialSwarmDemo"
        component={TrialSwarmDemo}
        durationInFrames={DEMO_TOTAL_FRAMES}
        fps={DEMO_FPS}
        width={1920}
        height={1080}
      />
    </>
  );
};
