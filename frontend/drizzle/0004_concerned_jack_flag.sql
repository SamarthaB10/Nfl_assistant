ALTER TABLE "game_comments" DROP CONSTRAINT "game_comments_parent_comment_id_game_comments_id_fk";
--> statement-breakpoint
ALTER TABLE "game_comments" ADD CONSTRAINT "game_comments_parent_comment_id_game_comments_id_fk" FOREIGN KEY ("parent_comment_id") REFERENCES "public"."game_comments"("id") ON DELETE cascade ON UPDATE no action;