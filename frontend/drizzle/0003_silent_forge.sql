CREATE TABLE "game_comments" (
	"id" bigserial PRIMARY KEY NOT NULL,
	"game_key" text NOT NULL,
	"user_id" text NOT NULL,
	"parent_comment_id" bigint,
	"body" text NOT NULL,
	"is_deleted" boolean DEFAULT false NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
ALTER TABLE "game_comments" ADD CONSTRAINT "game_comments_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "game_comments" ADD CONSTRAINT "game_comments_parent_comment_id_game_comments_id_fk" FOREIGN KEY ("parent_comment_id") REFERENCES "public"."game_comments"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "game_comments_game_cursor_idx" ON "game_comments" USING btree ("game_key","created_at" DESC NULLS LAST,"id" DESC NULLS LAST);--> statement-breakpoint
CREATE INDEX "game_comments_parent_created_idx" ON "game_comments" USING btree ("parent_comment_id","created_at","id");--> statement-breakpoint
CREATE INDEX "game_comments_user_id_idx" ON "game_comments" USING btree ("user_id");