/**
 * Mirrors the Pydantic models in backend/app/models. Keep these two in sync
 * when adding fields. (A codegen step is on the wishlist — see ARCHITECTURE.md.)
 */

export type ChatRole = "user" | "assistant";
export type ChatMode = "cards" | "rules";

export interface ChatMessage {
  role: ChatRole;
  content: string;
}

export interface CardImageUris {
  small?: string;
  normal?: string;
  large?: string;
  png?: string;
  art_crop?: string;
  border_crop?: string;
}

export interface Card {
  id: string;
  oracle_id?: string;
  name: string;
  mana_cost?: string;
  cmc?: number;
  type_line?: string;
  oracle_text?: string;
  colors?: string[];
  color_identity?: string[];
  power?: string;
  toughness?: string;
  loyalty?: string;
  rarity?: string;
  set?: string;
  set_name?: string;
  collector_number?: string;
  image_uris?: CardImageUris;
  scryfall_uri?: string;
  legalities?: Record<string, string>;
}

export interface ChatRequest {
  messages: ChatMessage[];
  mode?: ChatMode;
  preferences?: Record<string, string>;
}

export interface ChatResponse {
  reply: string;
  cards: Card[];
  stop_reason?: string | null;
}
