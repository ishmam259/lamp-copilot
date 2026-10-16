"use client";

import { PageTitle } from "@/components/carton";
import { LiveLog } from "@/components/live-log";

export default function LogPage() {
  return (
    <div>
      <PageTitle
        title="Audit log"
        sub="Every event, as it happens: what was read, proposed, approved and paid. T1 is you and the AI, T2 the calculations, T3 anything touching money."
      />
      <div className="h-[calc(100dvh-14rem)] overflow-hidden rounded-[8px] border border-rule bg-board lg:h-[calc(100dvh-12rem)]">
        <LiveLog />
      </div>
    </div>
  );
}
