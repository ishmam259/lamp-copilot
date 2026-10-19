"use client";

import { PageTitle } from "@/components/carton";
import { LiveLog } from "@/components/live-log";

export default function LogPage() {
  return (
    <div>
      <PageTitle
        title="Audit log"
      />
      <div className="h-[calc(100dvh-14rem)] overflow-hidden rounded-[8px] border border-rule bg-board lg:h-[calc(100dvh-12rem)]">
        <LiveLog />
      </div>
    </div>
  );
}
