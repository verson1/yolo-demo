-- Run once only if an older yolo_template database already exists.
USE yolo_template;

ALTER TABLE detect_record
    ADD COLUMN model_id VARCHAR(80) NOT NULL DEFAULT 'legacy' AFTER detect_type,
    ADD COLUMN helmet_count INT UNSIGNED NOT NULL DEFAULT 0 AFTER total_objects,
    ADD COLUMN no_helmet_count INT UNSIGNED NOT NULL DEFAULT 0 AFTER helmet_count,
    ADD COLUMN violation_frames INT UNSIGNED NOT NULL DEFAULT 0 AFTER no_helmet_count,
    ADD INDEX idx_record_model_created (model_id, created_at);
