CREATE DATABASE IF NOT EXISTS yolo_template CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE yolo_template;

CREATE TABLE IF NOT EXISTS detect_record (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    detect_type VARCHAR(20) NOT NULL,
    model_id VARCHAR(80) NOT NULL,
    original_path VARCHAR(255) NOT NULL,
    result_path VARCHAR(255) NOT NULL,
    total_objects INT UNSIGNED NOT NULL DEFAULT 0,
    helmet_count INT UNSIGNED NOT NULL DEFAULT 0,
    no_helmet_count INT UNSIGNED NOT NULL DEFAULT 0,
    violation_frames INT UNSIGNED NOT NULL DEFAULT 0,
    elapsed_ms INT UNSIGNED NOT NULL DEFAULT 0,
    confidence FLOAT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_record_created_at (created_at),
    INDEX idx_record_type_created (detect_type, created_at),
    INDEX idx_record_model_created (model_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS detect_object (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    record_id BIGINT UNSIGNED NOT NULL,
    frame_index INT UNSIGNED NULL COMMENT 'NULL for images; zero-based frame for videos',
    class_id INT NOT NULL,
    class_name VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    x1 FLOAT NOT NULL,
    y1 FLOAT NOT NULL,
    x2 FLOAT NOT NULL,
    y2 FLOAT NOT NULL,
    INDEX idx_object_record (record_id),
    INDEX idx_object_class (class_name),
    CONSTRAINT fk_object_record FOREIGN KEY (record_id) REFERENCES detect_record(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
