CREATE TABLE "news_articles" (
	"id" bigserial PRIMARY KEY NOT NULL,
	"source" text NOT NULL,
	"source_article_id" text NOT NULL,
	"title" text NOT NULL,
	"author" text,
	"excerpt" text,
	"canonical_url" text NOT NULL,
	"image_url" text,
	"team_codes" text[] NOT NULL,
	"published_at" timestamp with time zone NOT NULL,
	"fetched_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX "news_articles_source_article_unique" ON "news_articles" USING btree ("source","source_article_id");--> statement-breakpoint
CREATE UNIQUE INDEX "news_articles_canonical_url_unique" ON "news_articles" USING btree ("canonical_url");--> statement-breakpoint
CREATE INDEX "news_articles_cursor_idx" ON "news_articles" USING btree ("published_at" DESC NULLS LAST,"id" DESC NULLS LAST);--> statement-breakpoint
CREATE INDEX "news_articles_source_cursor_idx" ON "news_articles" USING btree ("source","published_at" DESC NULLS LAST,"id" DESC NULLS LAST);--> statement-breakpoint
CREATE INDEX "news_articles_team_codes_idx" ON "news_articles" USING gin ("team_codes");