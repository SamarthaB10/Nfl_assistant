import type { Metadata } from "next";

import { HeadlinesWorkspace } from "@/components/headlines/headlines-workspace";

export const metadata: Metadata = {
  title: "NFL Live News | Drizzle",
  description:
    "Current NFL news from ESPN, CBS Sports, and FOX Sports in one live feed.",
};

export default function HeadlinesPage() {
  return <HeadlinesWorkspace />;
}
