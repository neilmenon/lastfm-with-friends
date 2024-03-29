-- MariaDB dump 10.19  Distrib 10.6.4-MariaDB, for osx10.17 (arm64)
--
-- Host: localhost    Database: lastfm_with_friends
-- ------------------------------------------------------
-- Server version	10.6.4-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `albums`
--

DROP TABLE IF EXISTS `albums`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `albums` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `artist_name` varchar(400) NOT NULL,
  `name` varchar(500) NOT NULL,
  `url` varchar(2000) NOT NULL,
  `image_url` varchar(191) NOT NULL,
  PRIMARY KEY (`id`,`artist_name`(25),`name`(50)) USING BTREE,
  KEY `artist_name` (`artist_name`),
  CONSTRAINT `albums_ibfk_1` FOREIGN KEY (`artist_name`) REFERENCES `artists` (`name`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `artist_genres`
--

DROP TABLE IF EXISTS `artist_genres`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `artist_genres` (
  `artist_id` bigint(20) NOT NULL,
  `genre_id` int(11) NOT NULL,
  PRIMARY KEY (`artist_id`,`genre_id`),
  KEY `artist_genres_ibfk_2` (`genre_id`),
  CONSTRAINT `artist_genres_ibfk_1` FOREIGN KEY (`artist_id`) REFERENCES `artists` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `artist_genres_ibfk_2` FOREIGN KEY (`genre_id`) REFERENCES `genres` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `artist_redirects`
--

DROP TABLE IF EXISTS `artist_redirects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `artist_redirects` (
  `artist_name` varchar(400) NOT NULL,
  `redirected_name` varchar(400) NOT NULL,
  PRIMARY KEY (`artist_name`(25),`redirected_name`(25)) USING BTREE,
  KEY `redirected_name` (`redirected_name`),
  CONSTRAINT `artist_redirects_ibfk_1` FOREIGN KEY (`redirected_name`) REFERENCES `artists` (`name`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `artists`
--

DROP TABLE IF EXISTS `artists`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `artists` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(400) NOT NULL,
  `url` varchar(2000) DEFAULT NULL,
  `image_url` varchar(191) DEFAULT NULL,
  `listeners` int(11) DEFAULT NULL,
  `playcount` int(11) DEFAULT NULL,
  `name_sanitized` varchar(400) GENERATED ALWAYS AS (ucase(replace(replace(replace(`name`,'"',''),'\'',''),'•',' '))) VIRTUAL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `name_sanitized` (`name_sanitized`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `genres`
--

DROP TABLE IF EXISTS `genres`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `genres` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(191) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `group_sessions`
--

DROP TABLE IF EXISTS `group_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `group_sessions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `owner` varchar(191) NOT NULL,
  `group_jc` varchar(191) NOT NULL,
  `is_silent` tinyint(1) NOT NULL,
  `created` datetime NOT NULL,
  PRIMARY KEY (`id`,`owner`),
  KEY `fk_owner` (`owner`),
  KEY `fk_group_jc` (`group_jc`),
  CONSTRAINT `fk_group_jc` FOREIGN KEY (`group_jc`) REFERENCES `groups` (`join_code`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_owner` FOREIGN KEY (`owner`) REFERENCES `users` (`username`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `groups`
--

DROP TABLE IF EXISTS `groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(400) NOT NULL,
  `description` varchar(400) NOT NULL,
  `created` datetime NOT NULL,
  `owner` varchar(191) NOT NULL,
  `join_code` varchar(191) NOT NULL,
  PRIMARY KEY (`id`,`owner`,`join_code`),
  UNIQUE KEY `join_code` (`join_code`),
  KEY `foreign_key_owner` (`owner`),
  CONSTRAINT `foreign_key_owner` FOREIGN KEY (`owner`) REFERENCES `users` (`username`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `now_playing`
--

DROP TABLE IF EXISTS `now_playing`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `now_playing` (
  `username` varchar(191) NOT NULL,
  `check_count` int(11) DEFAULT NULL,
  `artist` varchar(400) NOT NULL,
  `track` varchar(1000) NOT NULL,
  `album` varchar(500) NOT NULL,
  `timestamp` int(11) NOT NULL,
  `url` varchar(2000) NOT NULL,
  `image_url` varchar(191) NOT NULL,
  PRIMARY KEY (`username`),
  CONSTRAINT `now_playing_ibfk_1` FOREIGN KEY (`username`) REFERENCES `users` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `personal_stats`
--

DROP TABLE IF EXISTS `personal_stats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `personal_stats` (
  `username` varchar(191) NOT NULL,
  `cant_get_enough` varchar(2000) DEFAULT NULL,
  `most_active_hour` int(11) NOT NULL,
  `scrobble_compare` varchar(2000) NOT NULL,
  `top_genre` varchar(2000) NOT NULL,
  `top_rising` varchar(2000) NOT NULL,
  `time_period_days` int(1) NOT NULL,
  `date_generated` datetime NOT NULL,
  PRIMARY KEY (`username`),
  CONSTRAINT `personal_stats_ibfk_1` FOREIGN KEY (`username`) REFERENCES `users` (`username`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sessions`
--

DROP TABLE IF EXISTS `sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sessions` (
  `username` varchar(192) NOT NULL,
  `session_key` varchar(191) NOT NULL,
  `last_used` datetime DEFAULT NULL,
  PRIMARY KEY (`session_key`),
  UNIQUE KEY `session_key` (`session_key`),
  KEY `user_sessions` (`username`),
  CONSTRAINT `user_sessions` FOREIGN KEY (`username`) REFERENCES `users` (`username`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `stats`
--

DROP TABLE IF EXISTS `stats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `stats` (
  `date` datetime NOT NULL,
  `artists` bigint(20) NOT NULL,
  `albums` bigint(20) NOT NULL,
  `tracks` bigint(20) NOT NULL,
  `scrobbles` bigint(20) NOT NULL,
  `users` int(11) NOT NULL,
  `groups` int(11) NOT NULL,
  `genres` int(11) DEFAULT NULL,
  UNIQUE KEY `date` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tasks`
--

DROP TABLE IF EXISTS `tasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tasks` (
  `name` varchar(191) NOT NULL,
  `last_finished` datetime DEFAULT current_timestamp(),
  `skips` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `track_scrobbles`
--

DROP TABLE IF EXISTS `track_scrobbles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `track_scrobbles` (
  `artist_id` bigint(20) NOT NULL,
  `album_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `track` varchar(400) NOT NULL,
  `timestamp` varchar(12) NOT NULL,
  `track_sanitized` varchar(400) GENERATED ALWAYS AS (ucase(replace(replace(replace(`track`,'"',''),'\'',''),'•',' '))) VIRTUAL,
  PRIMARY KEY (`artist_id`,`album_id`,`user_id`,`track`(50),`timestamp`(11)) USING BTREE,
  KEY `album_id` (`album_id`),
  KEY `user_id` (`user_id`),
  KEY `idx_timestamp` (`user_id`,`timestamp`) USING BTREE,
  KEY `album_id_track` (`album_id`,`track`),
  KEY `wk_track` (`artist_id`,`track_sanitized`) USING BTREE,
  KEY `timestamp` (`timestamp`),
  CONSTRAINT `track_scrobbles_ibfk_1` FOREIGN KEY (`artist_id`) REFERENCES `artists` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `track_scrobbles_ibfk_2` FOREIGN KEY (`album_id`) REFERENCES `albums` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `track_scrobbles_ibfk_3` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_group_sessions`
--

DROP TABLE IF EXISTS `user_group_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_group_sessions` (
  `username` varchar(191) NOT NULL,
  `session_id` int(11) NOT NULL,
  `last_timestamp` varchar(191) NOT NULL,
  PRIMARY KEY (`username`,`session_id`),
  KEY `fk_session_id` (`session_id`),
  CONSTRAINT `fk_session_id` FOREIGN KEY (`session_id`) REFERENCES `group_sessions` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_username` FOREIGN KEY (`username`) REFERENCES `users` (`username`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_groups`
--

DROP TABLE IF EXISTS `user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_groups` (
  `username` varchar(191) NOT NULL,
  `group_jc` varchar(191) NOT NULL,
  `joined` datetime NOT NULL,
  PRIMARY KEY (`username`,`group_jc`),
  KEY `foreign_key_join_code` (`group_jc`),
  CONSTRAINT `foreign_key_join_code` FOREIGN KEY (`group_jc`) REFERENCES `groups` (`join_code`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `foreign_key_username` FOREIGN KEY (`username`) REFERENCES `users` (`username`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(191) CHARACTER SET utf8mb4 NOT NULL,
  `display_name` varchar(191) CHARACTER SET utf8mb4 NOT NULL,
  `registered` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `joined_date` datetime NOT NULL DEFAULT current_timestamp(),
  `profile_image` varchar(191) CHARACTER SET utf8mb4 NOT NULL,
  `scrobbles` bigint(20) NOT NULL,
  `last_update` datetime DEFAULT NULL,
  `progress` float NOT NULL,
  `settings` text COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`user_id`,`username`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2022-02-04 19:11:27
