import type { UIMessage } from "ai";

import type { NormalizedQueryResponse } from "./gateway-client";

export type DemoChatMetadata = {
  trace?: NormalizedQueryResponse;
};

export type DemoChatMessage = UIMessage<DemoChatMetadata>;
