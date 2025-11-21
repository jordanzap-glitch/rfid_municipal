-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Nov 21, 2025 at 05:47 AM
-- Server version: 12.0.2-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `municipal_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `app_academic_year`
--

CREATE TABLE `app_academic_year` (
  `id` bigint(20) NOT NULL,
  `year` date NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `semester_id` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_academic_year`
--

INSERT INTO `app_academic_year` (`id`, `year`, `is_active`, `semester_id`) VALUES
(1, '2026-01-01', 1, 2);

-- --------------------------------------------------------

--
-- Table structure for table `app_barangay`
--

CREATE TABLE `app_barangay` (
  `id` bigint(20) NOT NULL,
  `barangay_name` varchar(100) NOT NULL,
  `municipality_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_barangay`
--

INSERT INTO `app_barangay` (`id`, `barangay_name`, `municipality_id`) VALUES
(1, 'Becuran', 1),
(2, 'Dila-dila', 1),
(3, 'San Agustin', 1),
(4, 'San Basilio', 1),
(5, 'San Isidro', 1),
(6, 'San Jose', 1),
(7, 'San Juan', 1),
(8, 'San Jose', 1),
(9, 'San Matias', 1),
(10, 'Santa Monica', 1),
(11, 'San Vicente', 1);

-- --------------------------------------------------------

--
-- Table structure for table `app_bsrcenter`
--

CREATE TABLE `app_bsrcenter` (
  `id` bigint(20) NOT NULL,
  `age` int(11) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `date_claimed` date NOT NULL,
  `date_claim_expiry` date NOT NULL,
  `registration_id` bigint(20) NOT NULL,
  `barangay_indigency` tinyint(1) NOT NULL,
  `barangay_recidency` tinyint(1) NOT NULL,
  `tracking_number` varchar(100) DEFAULT NULL,
  `diagnosis` longtext DEFAULT NULL,
  `status_id` bigint(20) NOT NULL,
  `processed_by_id` bigint(20) DEFAULT NULL,
  `actioned_at` datetime(6) DEFAULT NULL,
  `actioned_by_id` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_bsrcenter`
--

INSERT INTO `app_bsrcenter` (`id`, `age`, `amount`, `date_claimed`, `date_claim_expiry`, `registration_id`, `barangay_indigency`, `barangay_recidency`, `tracking_number`, `diagnosis`, `status_id`, `processed_by_id`, `actioned_at`, `actioned_by_id`) VALUES
(3, 28, 1000.00, '2025-11-21', '2025-11-22', 1, 1, 1, 'CC-M-1B73DE09FB', 'asdasd', 1, 3, '2025-11-21 04:46:05.080647', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `app_bsrcenter_burial`
--

CREATE TABLE `app_bsrcenter_burial` (
  `id` bigint(20) NOT NULL,
  `tracking_number` varchar(100) DEFAULT NULL,
  `deceased_name` varchar(255) NOT NULL,
  `relationship` varchar(100) NOT NULL,
  `date_claimed` date NOT NULL,
  `date_claim_expiry` date NOT NULL,
  `status_id` bigint(20) NOT NULL,
  `death_certificate` tinyint(1) NOT NULL,
  `cause_of_death` longtext DEFAULT NULL,
  `amount` decimal(10,2) NOT NULL,
  `registration_id` bigint(20) NOT NULL,
  `processed_by_id` bigint(20) DEFAULT NULL,
  `actioned_at` datetime(6) DEFAULT NULL,
  `actioned_by_id` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_bsrcenter_burial`
--

INSERT INTO `app_bsrcenter_burial` (`id`, `tracking_number`, `deceased_name`, `relationship`, `date_claimed`, `date_claim_expiry`, `status_id`, `death_certificate`, `cause_of_death`, `amount`, `registration_id`, `processed_by_id`, `actioned_at`, `actioned_by_id`) VALUES
(1, 'CC-B-D01026A88D', 'test', 'testing', '2025-11-20', '2025-12-22', 2, 1, 'accident', 1000.00, 1, 3, '2025-11-21 04:07:15.491843', 6);

-- --------------------------------------------------------

--
-- Table structure for table `app_bsrcenter_meds`
--

CREATE TABLE `app_bsrcenter_meds` (
  `id` bigint(20) NOT NULL,
  `bsrcenter_id` bigint(20) NOT NULL,
  `medicines_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_bsrcenter_meds`
--

INSERT INTO `app_bsrcenter_meds` (`id`, `bsrcenter_id`, `medicines_id`) VALUES
(5, 3, 1),
(6, 3, 2);

-- --------------------------------------------------------

--
-- Table structure for table `app_civil_status`
--

CREATE TABLE `app_civil_status` (
  `id` bigint(20) NOT NULL,
  `civil_status_name` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_civil_status`
--

INSERT INTO `app_civil_status` (`id`, `civil_status_name`) VALUES
(1, 'Single'),
(2, 'Married'),
(3, 'Single Parent');

-- --------------------------------------------------------

--
-- Table structure for table `app_customuser`
--

CREATE TABLE `app_customuser` (
  `id` bigint(20) NOT NULL,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `user_type` varchar(25) NOT NULL,
  `profile_pic` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_customuser`
--

INSERT INTO `app_customuser` (`id`, `password`, `last_login`, `is_superuser`, `username`, `first_name`, `last_name`, `is_staff`, `is_active`, `date_joined`, `user_type`, `profile_pic`, `email`) VALUES
(1, 'pbkdf2_sha256$1000000$iw9RDgSkP5CqYXaoJKU918$+WlM7+GLAQQtum7Pr8X5RvfErzwbhIujyirYjBzH/ls=', '2025-11-20 14:56:08.380688', 1, 'superadmin', '', '', 1, 1, '2025-11-20 12:19:38.603359', '', '', 'admin@gmail.com'),
(2, 'pbkdf2_sha256$1000000$BUBRbW7zzRwxefppZpf9So$djGtOw5Ses9hZ6Wsv1rqJh/Um5E2HaCOaa+R/1dptoI=', '2025-11-21 02:25:47.752666', 0, 'staff_peso', 'anthony', 'Gin', 0, 1, '2025-11-20 12:37:06.000000', '7', '', 'example1@gmail.com'),
(3, 'pbkdf2_sha256$1000000$Ln9F8f4w6gBjmSyw7cI6JM$8DlGGAjp8dQgCdQEunbvZN0XIULVFbNdrR326MjhT1M=', '2025-11-21 04:45:24.049985', 0, 'staff_center', 'joshua', 'Vodka', 0, 1, '2025-11-20 12:37:31.000000', '5', '', 'example02@gmail.com'),
(4, 'pbkdf2_sha256$1000000$WUww8qURatMATV1HB0WEbD$LitnNutXql34CWHH7nHU+fGgetwvrrDB4VXtgQ4BAR0=', '2025-11-21 00:54:11.258911', 0, 'jordan', '', '', 0, 1, '2025-11-20 12:38:00.201889', '2', '', 'jordan@gmail.com'),
(5, 'pbkdf2_sha256$1000000$bCUwhZ96EZDM0LJYrsJ5hC$ZaEtPxMTwtUp8aXVq8kmpR5a6MQE1y1FJ+1qmqXKF5E=', '2025-11-21 04:11:30.080413', 0, 'mun_admin', '', '', 0, 1, '2025-11-20 12:38:36.915069', '3', '', 'example@gmail.com'),
(6, 'pbkdf2_sha256$1000000$bRX3MTECrmLYJQ2hb1iuXZ$4ILC0q81tphq0nNEnOCJMPLHBociIPRymn5xCYvkKoY=', '2025-11-21 04:38:56.698378', 0, 'admin_center', '', '', 0, 1, '2025-11-20 12:39:34.962796', '4', '', 'example03@gmail.com'),
(7, 'pbkdf2_sha256$1000000$rSWAWy4LTVMXqoiDCcoOnd$eEdzABtM6j5/7db0QDztzJlVxXCoM2JFM1TsYvAAumo=', '2025-11-21 04:36:18.729317', 0, 'admin_peso', '', '', 0, 1, '2025-11-20 12:40:04.601063', '6', '', 'example4@gmail.com');

-- --------------------------------------------------------

--
-- Table structure for table `app_customuser_groups`
--

CREATE TABLE `app_customuser_groups` (
  `id` bigint(20) NOT NULL,
  `customuser_id` bigint(20) NOT NULL,
  `group_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `app_customuser_user_permissions`
--

CREATE TABLE `app_customuser_user_permissions` (
  `id` bigint(20) NOT NULL,
  `customuser_id` bigint(20) NOT NULL,
  `permission_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `app_end_user_type`
--

CREATE TABLE `app_end_user_type` (
  `id` bigint(20) NOT NULL,
  `end_user_type` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_end_user_type`
--

INSERT INTO `app_end_user_type` (`id`, `end_user_type`) VALUES
(1, 'Senior Citizen'),
(2, 'Student'),
(3, 'Regular');

-- --------------------------------------------------------

--
-- Table structure for table `app_medicines`
--

CREATE TABLE `app_medicines` (
  `id` bigint(20) NOT NULL,
  `medicine_name` varchar(255) NOT NULL,
  `dosage` varchar(100) NOT NULL,
  `frequency` varchar(100) NOT NULL,
  `date_expiry` date NOT NULL,
  `date_added` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_medicines`
--

INSERT INTO `app_medicines` (`id`, `medicine_name`, `dosage`, `frequency`, `date_expiry`, `date_added`) VALUES
(1, 'Biogesic', '12 mg', '3 times a day', '2025-11-20', '2025-11-20 12:31:07.047215'),
(2, 'Bio Flu', '12 mg', '3 times a day', '2025-11-20', '2025-11-20 12:31:29.161480');

-- --------------------------------------------------------

--
-- Table structure for table `app_municipality`
--

CREATE TABLE `app_municipality` (
  `id` bigint(20) NOT NULL,
  `municipality_name` varchar(100) NOT NULL,
  `province_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_municipality`
--

INSERT INTO `app_municipality` (`id`, `municipality_name`, `province_id`) VALUES
(1, 'Santa Rita', 1);

-- --------------------------------------------------------

--
-- Table structure for table `app_occupation`
--

CREATE TABLE `app_occupation` (
  `id` bigint(20) NOT NULL,
  `occupation_name` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_occupation`
--

INSERT INTO `app_occupation` (`id`, `occupation_name`) VALUES
(1, 'Farmer'),
(2, 'Construction Worker'),
(3, 'Unemployed'),
(4, 'Other');

-- --------------------------------------------------------

--
-- Table structure for table `app_peso_reap`
--

CREATE TABLE `app_peso_reap` (
  `id` bigint(20) NOT NULL,
  `biodata` tinyint(1) NOT NULL,
  `certificate_of_reg` tinyint(1) NOT NULL,
  `certificate_of_grades` tinyint(1) NOT NULL,
  `barangay_indigency` tinyint(1) NOT NULL,
  `barangay_recidency` tinyint(1) NOT NULL,
  `official_receipt` tinyint(1) NOT NULL,
  `registration_id` bigint(20) NOT NULL,
  `processed_by_id` bigint(20) DEFAULT NULL,
  `date_added` date DEFAULT NULL,
  `is_released` tinyint(1) NOT NULL,
  `tracking_number` varchar(100) DEFAULT NULL,
  `status_id` bigint(20) NOT NULL,
  `Academic_year_id` bigint(20) DEFAULT NULL,
  `next` tinyint(1) NOT NULL,
  `reap_type_id` bigint(20) DEFAULT NULL,
  `actioned_at` datetime(6) DEFAULT NULL,
  `actioned_by_id` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_peso_reap`
--

INSERT INTO `app_peso_reap` (`id`, `biodata`, `certificate_of_reg`, `certificate_of_grades`, `barangay_indigency`, `barangay_recidency`, `official_receipt`, `registration_id`, `processed_by_id`, `date_added`, `is_released`, `tracking_number`, `status_id`, `Academic_year_id`, `next`, `reap_type_id`, `actioned_at`, `actioned_by_id`) VALUES
(1, 1, 1, 1, 1, 1, 1, 1, 2, '2025-11-20', 0, 'PESO-R-0418246B51', 2, 1, 0, 1, '2025-11-21 03:30:22.465460', NULL),
(2, 1, 1, 1, 1, 1, 1, 3, 2, '2025-11-21', 0, 'PESO-R-7A3547248E', 2, 1, 0, 1, '2025-11-21 04:09:17.749255', 7);

-- --------------------------------------------------------

--
-- Table structure for table `app_peso_tupad`
--

CREATE TABLE `app_peso_tupad` (
  `id` bigint(20) NOT NULL,
  `tracking_number` varchar(100) DEFAULT NULL,
  `date_issued` date NOT NULL,
  `date_issued_expiry` date NOT NULL,
  `name_of_beneficiary` varchar(255) NOT NULL,
  `is_released` tinyint(1) NOT NULL,
  `processed_by_id` bigint(20) DEFAULT NULL,
  `registration_id` bigint(20) NOT NULL,
  `status_id` bigint(20) NOT NULL,
  `skills_training_id` bigint(20) NOT NULL,
  `actioned_at` datetime(6) DEFAULT NULL,
  `actioned_by_id` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_peso_tupad`
--

INSERT INTO `app_peso_tupad` (`id`, `tracking_number`, `date_issued`, `date_issued_expiry`, `name_of_beneficiary`, `is_released`, `processed_by_id`, `registration_id`, `status_id`, `skills_training_id`, `actioned_at`, `actioned_by_id`) VALUES
(1, 'PESO-T-3140C3EC6E', '2025-11-20', '2026-11-20', 'ju', 0, 2, 3, 2, 1, '2025-11-21 04:09:05.079726', 7),
(2, 'PESO-T-8AAFE61003', '2025-11-21', '2025-11-22', 'HELLO', 1, 2, 1, 2, 1, '2025-11-21 03:30:22.553833', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `app_province`
--

CREATE TABLE `app_province` (
  `id` bigint(20) NOT NULL,
  `province_name` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_province`
--

INSERT INTO `app_province` (`id`, `province_name`) VALUES
(1, 'Pampanga');

-- --------------------------------------------------------

--
-- Table structure for table `app_reap_type`
--

CREATE TABLE `app_reap_type` (
  `id` bigint(20) NOT NULL,
  `type_name` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_reap_type`
--

INSERT INTO `app_reap_type` (`id`, `type_name`) VALUES
(1, 'NEW'),
(2, 'RENEW');

-- --------------------------------------------------------

--
-- Table structure for table `app_registration`
--

CREATE TABLE `app_registration` (
  `id` bigint(20) NOT NULL,
  `rfid` varchar(50) NOT NULL,
  `last_name` varchar(100) NOT NULL,
  `first_name` varchar(100) NOT NULL,
  `middle_name` varchar(100) DEFAULT NULL,
  `name_extension` varchar(10) DEFAULT NULL,
  `date_of_birth` date NOT NULL,
  `place_of_birth` varchar(255) NOT NULL,
  `mobile_no` varchar(20) NOT NULL,
  `date_added` datetime(6) NOT NULL,
  `barangay_id` bigint(20) NOT NULL,
  `municipality_id` bigint(20) NOT NULL,
  `province_id` bigint(20) NOT NULL,
  `profile_pic` varchar(100) DEFAULT NULL,
  `gender` varchar(10) DEFAULT NULL,
  `occupation_id` bigint(20) NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  `age` int(11) NOT NULL,
  `zone_street` varchar(200) DEFAULT NULL,
  `end_user_type_id` bigint(20) DEFAULT NULL,
  `civil_status_id` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_registration`
--

INSERT INTO `app_registration` (`id`, `rfid`, `last_name`, `first_name`, `middle_name`, `name_extension`, `date_of_birth`, `place_of_birth`, `mobile_no`, `date_added`, `barangay_id`, `municipality_id`, `province_id`, `profile_pic`, `gender`, `occupation_id`, `email`, `age`, `zone_street`, `end_user_type_id`, `civil_status_id`) VALUES
(1, '3871067652', 'Zap', 'Jord', 'Santos', '', '1997-10-20', 'becuran', '0912345678', '2025-11-20 13:00:49.445412', 1, 1, 1, 'profile_pic/member_6579cf2c032e4c5bbed74e93e3f3dd36.png', 'Male', 1, 'jordan@gmail.com', 28, 'zone 6', 2, 3),
(3, '3871894596', 'Santos', 'Gin', 'Vodka', 'jr', '1950-10-02', 'becuran', '09123456', '2025-11-20 13:04:24.694041', 2, 1, 1, 'profile_pic/member_1c28f62baaaf47a086761dba085373b0.png', 'Male', 2, 'old@gmail.com', 75, 'Zone 5', 1, 2);

-- --------------------------------------------------------

--
-- Table structure for table `app_rfidauth`
--

CREATE TABLE `app_rfidauth` (
  `id` bigint(20) NOT NULL,
  `rfid` varchar(50) NOT NULL,
  `status` varchar(10) NOT NULL,
  `in_use` tinyint(1) NOT NULL,
  `date_added` datetime(6) NOT NULL,
  `registration_id` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_rfidauth`
--

INSERT INTO `app_rfidauth` (`id`, `rfid`, `status`, `in_use`, `date_added`, `registration_id`) VALUES
(1, '3870455284', 'valid', 0, '2025-11-20 12:25:07.893803', NULL),
(2, '3871067652', 'invalid', 1, '2025-11-20 12:25:21.247123', 1),
(3, '3870246628', 'valid', 0, '2025-11-20 12:25:25.629003', NULL),
(4, '3871894596', 'invalid', 1, '2025-11-20 12:25:29.166192', 3);

-- --------------------------------------------------------

--
-- Table structure for table `app_semester`
--

CREATE TABLE `app_semester` (
  `id` bigint(20) NOT NULL,
  `sem_name` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_semester`
--

INSERT INTO `app_semester` (`id`, `sem_name`) VALUES
(1, '1st Semester'),
(2, '2nd Semester');

-- --------------------------------------------------------

--
-- Table structure for table `app_skills_training`
--

CREATE TABLE `app_skills_training` (
  `id` bigint(20) NOT NULL,
  `Skills_name` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_skills_training`
--

INSERT INTO `app_skills_training` (`id`, `Skills_name`) VALUES
(1, 'Agriculutre');

-- --------------------------------------------------------

--
-- Table structure for table `app_status`
--

CREATE TABLE `app_status` (
  `id` bigint(20) NOT NULL,
  `status_name` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_status`
--

INSERT INTO `app_status` (`id`, `status_name`) VALUES
(1, 'Pending'),
(2, 'Approved'),
(3, 'Rejected');

-- --------------------------------------------------------

--
-- Table structure for table `auth_group`
--

CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL,
  `name` varchar(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `auth_group_permissions`
--

CREATE TABLE `auth_group_permissions` (
  `id` bigint(20) NOT NULL,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `auth_permission`
--

CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `auth_permission`
--

INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES
(1, 'Can add log entry', 1, 'add_logentry'),
(2, 'Can change log entry', 1, 'change_logentry'),
(3, 'Can delete log entry', 1, 'delete_logentry'),
(4, 'Can view log entry', 1, 'view_logentry'),
(5, 'Can add permission', 2, 'add_permission'),
(6, 'Can change permission', 2, 'change_permission'),
(7, 'Can delete permission', 2, 'delete_permission'),
(8, 'Can view permission', 2, 'view_permission'),
(9, 'Can add group', 3, 'add_group'),
(10, 'Can change group', 3, 'change_group'),
(11, 'Can delete group', 3, 'delete_group'),
(12, 'Can view group', 3, 'view_group'),
(13, 'Can add content type', 4, 'add_contenttype'),
(14, 'Can change content type', 4, 'change_contenttype'),
(15, 'Can delete content type', 4, 'delete_contenttype'),
(16, 'Can view content type', 4, 'view_contenttype'),
(17, 'Can add session', 5, 'add_session'),
(18, 'Can change session', 5, 'change_session'),
(19, 'Can delete session', 5, 'delete_session'),
(20, 'Can view session', 5, 'view_session'),
(21, 'Can add user', 6, 'add_customuser'),
(22, 'Can change user', 6, 'change_customuser'),
(23, 'Can delete user', 6, 'delete_customuser'),
(24, 'Can view user', 6, 'view_customuser'),
(25, 'Can add barangay', 7, 'add_barangay'),
(26, 'Can change barangay', 7, 'change_barangay'),
(27, 'Can delete barangay', 7, 'delete_barangay'),
(28, 'Can view barangay', 7, 'view_barangay'),
(29, 'Can add municipality', 8, 'add_municipality'),
(30, 'Can change municipality', 8, 'change_municipality'),
(31, 'Can delete municipality', 8, 'delete_municipality'),
(32, 'Can view municipality', 8, 'view_municipality'),
(33, 'Can add province', 9, 'add_province'),
(34, 'Can change province', 9, 'change_province'),
(35, 'Can delete province', 9, 'delete_province'),
(36, 'Can view province', 9, 'view_province'),
(37, 'Can add registration', 10, 'add_registration'),
(38, 'Can change registration', 10, 'change_registration'),
(39, 'Can delete registration', 10, 'delete_registration'),
(40, 'Can view registration', 10, 'view_registration'),
(41, 'Can add rfid auth', 11, 'add_rfidauth'),
(42, 'Can change rfid auth', 11, 'change_rfidauth'),
(43, 'Can delete rfid auth', 11, 'delete_rfidauth'),
(44, 'Can view rfid auth', 11, 'view_rfidauth'),
(45, 'Can add medicines', 12, 'add_medicines'),
(46, 'Can change medicines', 12, 'change_medicines'),
(47, 'Can delete medicines', 12, 'delete_medicines'),
(48, 'Can view medicines', 12, 'view_medicines'),
(49, 'Can add bsrcenter', 13, 'add_bsrcenter'),
(50, 'Can change bsrcenter', 13, 'change_bsrcenter'),
(51, 'Can delete bsrcenter', 13, 'delete_bsrcenter'),
(52, 'Can view bsrcenter', 13, 'view_bsrcenter'),
(53, 'Can add bsrcenter_meds', 14, 'add_bsrcenter_meds'),
(54, 'Can change bsrcenter_meds', 14, 'change_bsrcenter_meds'),
(55, 'Can delete bsrcenter_meds', 14, 'delete_bsrcenter_meds'),
(56, 'Can view bsrcenter_meds', 14, 'view_bsrcenter_meds'),
(57, 'Can add bsrcenter_ burial', 15, 'add_bsrcenter_burial'),
(58, 'Can change bsrcenter_ burial', 15, 'change_bsrcenter_burial'),
(59, 'Can delete bsrcenter_ burial', 15, 'delete_bsrcenter_burial'),
(60, 'Can view bsrcenter_ burial', 15, 'view_bsrcenter_burial'),
(61, 'Can add status', 16, 'add_status'),
(62, 'Can change status', 16, 'change_status'),
(63, 'Can delete status', 16, 'delete_status'),
(64, 'Can view status', 16, 'view_status'),
(65, 'Can add peso_reap', 17, 'add_peso_reap'),
(66, 'Can change peso_reap', 17, 'change_peso_reap'),
(67, 'Can delete peso_reap', 17, 'delete_peso_reap'),
(68, 'Can view peso_reap', 17, 'view_peso_reap'),
(69, 'Can add skills_training', 18, 'add_skills_training'),
(70, 'Can change skills_training', 18, 'change_skills_training'),
(71, 'Can delete skills_training', 18, 'delete_skills_training'),
(72, 'Can view skills_training', 18, 'view_skills_training'),
(73, 'Can add peso_tupad', 19, 'add_peso_tupad'),
(74, 'Can change peso_tupad', 19, 'change_peso_tupad'),
(75, 'Can delete peso_tupad', 19, 'delete_peso_tupad'),
(76, 'Can view peso_tupad', 19, 'view_peso_tupad'),
(77, 'Can add academic_year', 20, 'add_academic_year'),
(78, 'Can change academic_year', 20, 'change_academic_year'),
(79, 'Can delete academic_year', 20, 'delete_academic_year'),
(80, 'Can view academic_year', 20, 'view_academic_year'),
(81, 'Can add semester', 21, 'add_semester'),
(82, 'Can change semester', 21, 'change_semester'),
(83, 'Can delete semester', 21, 'delete_semester'),
(84, 'Can view semester', 21, 'view_semester'),
(85, 'Can add end_user_type', 22, 'add_end_user_type'),
(86, 'Can change end_user_type', 22, 'change_end_user_type'),
(87, 'Can delete end_user_type', 22, 'delete_end_user_type'),
(88, 'Can view end_user_type', 22, 'view_end_user_type'),
(89, 'Can add reap_type', 23, 'add_reap_type'),
(90, 'Can change reap_type', 23, 'change_reap_type'),
(91, 'Can delete reap_type', 23, 'delete_reap_type'),
(92, 'Can view reap_type', 23, 'view_reap_type'),
(93, 'Can add occupation', 24, 'add_occupation'),
(94, 'Can change occupation', 24, 'change_occupation'),
(95, 'Can delete occupation', 24, 'delete_occupation'),
(96, 'Can view occupation', 24, 'view_occupation'),
(97, 'Can add civil_status', 25, 'add_civil_status'),
(98, 'Can change civil_status', 25, 'change_civil_status'),
(99, 'Can delete civil_status', 25, 'delete_civil_status'),
(100, 'Can view civil_status', 25, 'view_civil_status');

-- --------------------------------------------------------

--
-- Table structure for table `django_admin_log`
--

CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext DEFAULT NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) UNSIGNED NOT NULL CHECK (`action_flag` >= 0),
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `django_admin_log`
--

INSERT INTO `django_admin_log` (`id`, `action_time`, `object_id`, `object_repr`, `action_flag`, `change_message`, `content_type_id`, `user_id`) VALUES
(1, '2025-11-20 12:25:07.896138', '1', '3870455284 - valid - In Use', 1, '[{\"added\": {}}]', 11, 1),
(2, '2025-11-20 12:25:12.509563', '1', '3870455284 - valid - Not In Use', 2, '[{\"changed\": {\"fields\": [\"In use\"]}}]', 11, 1),
(3, '2025-11-20 12:25:21.248044', '2', '3871067652 - valid - Not In Use', 1, '[{\"added\": {}}]', 11, 1),
(4, '2025-11-20 12:25:25.630055', '3', '3870246628 - valid - Not In Use', 1, '[{\"added\": {}}]', 11, 1),
(5, '2025-11-20 12:25:29.167317', '4', '3871894596 - valid - Not In Use', 1, '[{\"added\": {}}]', 11, 1),
(6, '2025-11-20 12:25:41.304927', '1', 'Pampanga', 1, '[{\"added\": {}}]', 9, 1),
(7, '2025-11-20 12:26:08.775045', '1', 'Santa Rita', 1, '[{\"added\": {}}]', 8, 1),
(8, '2025-11-20 12:26:18.471149', '1', 'Becuran', 1, '[{\"added\": {}}]', 7, 1),
(9, '2025-11-20 12:26:28.239408', '2', 'Dila-dila', 1, '[{\"added\": {}}]', 7, 1),
(10, '2025-11-20 12:29:45.711111', '3', 'San Agustin', 1, '[{\"added\": {}}]', 7, 1),
(11, '2025-11-20 12:29:55.974938', '4', 'San Basilio', 1, '[{\"added\": {}}]', 7, 1),
(12, '2025-11-20 12:30:03.647926', '5', 'San Isidro', 1, '[{\"added\": {}}]', 7, 1),
(13, '2025-11-20 12:30:10.026657', '6', 'San Jose', 1, '[{\"added\": {}}]', 7, 1),
(14, '2025-11-20 12:30:17.588190', '7', 'San Juan', 1, '[{\"added\": {}}]', 7, 1),
(15, '2025-11-20 12:30:23.984909', '8', 'San Jose', 1, '[{\"added\": {}}]', 7, 1),
(16, '2025-11-20 12:30:32.916208', '9', 'San Matias', 1, '[{\"added\": {}}]', 7, 1),
(17, '2025-11-20 12:30:41.198126', '10', 'Santa Monica', 1, '[{\"added\": {}}]', 7, 1),
(18, '2025-11-20 12:30:48.457091', '11', 'San Vicente', 1, '[{\"added\": {}}]', 7, 1),
(19, '2025-11-20 12:31:07.050965', '1', 'Biogesic', 1, '[{\"added\": {}}]', 12, 1),
(20, '2025-11-20 12:31:29.162431', '2', 'Bio Flu', 1, '[{\"added\": {}}]', 12, 1),
(21, '2025-11-20 12:34:41.507140', '1', 'Senior Citizen', 1, '[{\"added\": {}}]', 22, 1),
(22, '2025-11-20 12:34:44.975683', '2', 'Student', 1, '[{\"added\": {}}]', 22, 1),
(23, '2025-11-20 12:34:51.893716', '3', 'Regular', 1, '[{\"added\": {}}]', 22, 1),
(24, '2025-11-20 12:35:13.708009', '1', 'Pending', 1, '[{\"added\": {}}]', 16, 1),
(25, '2025-11-20 12:35:16.989666', '2', 'Approved', 1, '[{\"added\": {}}]', 16, 1),
(26, '2025-11-20 12:35:25.254740', '3', 'Rejected', 1, '[{\"added\": {}}]', 16, 1),
(27, '2025-11-20 12:35:35.829016', '1', '1st Semester', 1, '[{\"added\": {}}]', 21, 1),
(28, '2025-11-20 12:35:40.671877', '2', '2nd Semester', 1, '[{\"added\": {}}]', 21, 1),
(29, '2025-11-20 12:36:08.414732', '1', '2026-01-01', 1, '[{\"added\": {}}]', 20, 1),
(30, '2025-11-20 12:37:07.271175', '2', 'staff_peso', 1, '[{\"added\": {}}]', 6, 1),
(31, '2025-11-20 12:37:32.933323', '3', 'staff_center', 1, '[{\"added\": {}}]', 6, 1),
(32, '2025-11-20 12:38:01.229301', '4', 'jordan', 1, '[{\"added\": {}}]', 6, 1),
(33, '2025-11-20 12:38:37.946103', '5', 'mun_admin', 1, '[{\"added\": {}}]', 6, 1),
(34, '2025-11-20 12:39:35.996770', '6', 'admin_center', 1, '[{\"added\": {}}]', 6, 1),
(35, '2025-11-20 12:40:05.641486', '7', 'admin_peso', 1, '[{\"added\": {}}]', 6, 1),
(36, '2025-11-20 12:44:08.707862', '1', 'Farmer', 1, '[{\"added\": {}}]', 24, 1),
(37, '2025-11-20 12:44:17.431911', '2', 'Construction Worker', 1, '[{\"added\": {}}]', 24, 1),
(38, '2025-11-20 12:44:22.536785', '3', 'Unemployed', 1, '[{\"added\": {}}]', 24, 1),
(39, '2025-11-20 12:44:27.474187', '4', 'Other', 1, '[{\"added\": {}}]', 24, 1),
(40, '2025-11-20 12:49:01.569805', '1', 'Single', 1, '[{\"added\": {}}]', 25, 1),
(41, '2025-11-20 12:49:07.282443', '2', 'Married', 1, '[{\"added\": {}}]', 25, 1),
(42, '2025-11-20 12:49:36.001084', '3', 'Single Parent', 1, '[{\"added\": {}}]', 25, 1),
(43, '2025-11-20 13:21:06.905911', '1', 'Agriculutre', 1, '[{\"added\": {}}]', 18, 1),
(44, '2025-11-20 14:56:49.663477', '3', 'staff_center', 2, '[{\"changed\": {\"fields\": [\"First name\", \"Last name\"]}}]', 6, 1),
(45, '2025-11-20 14:57:02.500996', '2', 'staff_peso', 2, '[{\"changed\": {\"fields\": [\"First name\", \"Last name\"]}}]', 6, 1);

-- --------------------------------------------------------

--
-- Table structure for table `django_content_type`
--

CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `django_content_type`
--

INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES
(1, 'admin', 'logentry'),
(20, 'app', 'academic_year'),
(7, 'app', 'barangay'),
(13, 'app', 'bsrcenter'),
(15, 'app', 'bsrcenter_burial'),
(14, 'app', 'bsrcenter_meds'),
(25, 'app', 'civil_status'),
(6, 'app', 'customuser'),
(22, 'app', 'end_user_type'),
(12, 'app', 'medicines'),
(8, 'app', 'municipality'),
(24, 'app', 'occupation'),
(17, 'app', 'peso_reap'),
(19, 'app', 'peso_tupad'),
(9, 'app', 'province'),
(23, 'app', 'reap_type'),
(10, 'app', 'registration'),
(11, 'app', 'rfidauth'),
(21, 'app', 'semester'),
(18, 'app', 'skills_training'),
(16, 'app', 'status'),
(3, 'auth', 'group'),
(2, 'auth', 'permission'),
(4, 'contenttypes', 'contenttype'),
(5, 'sessions', 'session');

-- --------------------------------------------------------

--
-- Table structure for table `django_migrations`
--

CREATE TABLE `django_migrations` (
  `id` bigint(20) NOT NULL,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `django_migrations`
--

INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES
(1, 'contenttypes', '0001_initial', '2025-11-20 12:18:58.017224'),
(2, 'contenttypes', '0002_remove_content_type_name', '2025-11-20 12:18:58.054622'),
(3, 'auth', '0001_initial', '2025-11-20 12:18:58.171851'),
(4, 'auth', '0002_alter_permission_name_max_length', '2025-11-20 12:18:58.214136'),
(5, 'auth', '0003_alter_user_email_max_length', '2025-11-20 12:18:58.221475'),
(6, 'auth', '0004_alter_user_username_opts', '2025-11-20 12:18:58.228006'),
(7, 'auth', '0005_alter_user_last_login_null', '2025-11-20 12:18:58.234299'),
(8, 'auth', '0006_require_contenttypes_0002', '2025-11-20 12:18:58.237168'),
(9, 'auth', '0007_alter_validators_add_error_messages', '2025-11-20 12:18:58.244314'),
(10, 'auth', '0008_alter_user_username_max_length', '2025-11-20 12:18:58.251438'),
(11, 'auth', '0009_alter_user_last_name_max_length', '2025-11-20 12:18:58.257751'),
(12, 'auth', '0010_alter_group_name_max_length', '2025-11-20 12:18:58.276111'),
(13, 'auth', '0011_update_proxy_permissions', '2025-11-20 12:18:58.283534'),
(14, 'auth', '0012_alter_user_first_name_max_length', '2025-11-20 12:18:58.292910'),
(15, 'app', '0001_initial', '2025-11-20 12:18:58.500415'),
(16, 'admin', '0001_initial', '2025-11-20 12:18:58.558560'),
(17, 'admin', '0002_logentry_remove_auto_add', '2025-11-20 12:18:58.567102'),
(18, 'admin', '0003_logentry_add_action_flag_choices', '2025-11-20 12:18:58.574951'),
(19, 'app', '0002_delete_membertype', '2025-11-20 12:18:58.585579'),
(20, 'app', '0003_alter_customuser_user_type', '2025-11-20 12:18:58.597627'),
(21, 'app', '0004_alter_customuser_user_type', '2025-11-20 12:18:58.653432'),
(22, 'app', '0005_alter_customuser_user_type', '2025-11-20 12:18:58.662364'),
(23, 'app', '0006_alter_customuser_user_type', '2025-11-20 12:18:58.671615'),
(24, 'app', '0007_alter_customuser_user_type', '2025-11-20 12:18:58.703725'),
(25, 'app', '0008_registration', '2025-11-20 12:18:58.716530'),
(26, 'app', '0009_alter_registration_id', '2025-11-20 12:18:58.740488'),
(27, 'app', '0010_rifdauth', '2025-11-20 12:18:58.751166'),
(28, 'app', '0011_barangay_municipality_province_delete_registration_and_more', '2025-11-20 12:18:58.838414'),
(29, 'app', '0012_registration', '2025-11-20 12:18:58.909599'),
(30, 'app', '0013_rename_municipality_id_barangay_municipality_and_more', '2025-11-20 12:19:00.553313'),
(31, 'app', '0014_registration_profile', '2025-11-20 12:19:00.572174'),
(32, 'app', '0015_rename_f_name_registration_first_name_and_more', '2025-11-20 12:19:00.623621'),
(33, 'app', '0016_rename_profile_registration_profile_pic', '2025-11-20 12:19:00.642865'),
(34, 'app', '0017_rename_rifdauth_rfidauth', '2025-11-20 12:19:00.669072'),
(35, 'app', '0018_medicines_registration_civil_status_and_more', '2025-11-20 12:19:00.814374'),
(36, 'app', '0019_registration_email', '2025-11-20 12:19:00.848735'),
(37, 'app', '0020_alter_registration_email_alter_registration_rfid', '2025-11-20 12:19:00.909532'),
(38, 'app', '0021_alter_customuser_user_type', '2025-11-20 12:19:00.918159'),
(39, 'app', '0022_alter_customuser_user_type', '2025-11-20 12:19:00.927595'),
(40, 'app', '0023_alter_customuser_user_type', '2025-11-20 12:19:00.937033'),
(41, 'app', '0024_delete_bsrcenter', '2025-11-20 12:19:00.949019'),
(42, 'app', '0025_bsrcenter', '2025-11-20 12:19:01.024280'),
(43, 'app', '0026_bsrcenter_status', '2025-11-20 12:19:01.056261'),
(44, 'app', '0027_remove_bsrcenter_medicines_and_more', '2025-11-20 12:19:01.505461'),
(45, 'app', '0028_bsrcenter_diagnosis_alter_bsrcenter_tracking_number', '2025-11-20 12:19:01.552434'),
(46, 'app', '0029_bsrcenter_burial', '2025-11-20 12:19:01.592136'),
(47, 'app', '0030_status', '2025-11-20 12:19:01.602532'),
(48, 'app', '0031_delete_status', '2025-11-20 12:19:01.613688'),
(49, 'app', '0032_status', '2025-11-20 12:19:01.623914'),
(50, 'app', '0033_remove_bsrcenter_status', '2025-11-20 12:19:01.645960'),
(51, 'app', '0034_bsrcenter_status', '2025-11-20 12:19:01.691836'),
(52, 'app', '0035_alter_bsrcenter_burial_status', '2025-11-20 12:19:01.786512'),
(53, 'app', '0036_alter_customuser_user_type', '2025-11-20 12:19:01.795230'),
(54, 'app', '0037_bsrcenter_released_by', '2025-11-20 12:19:01.836523'),
(55, 'app', '0038_bsrcenter_burial_released_by', '2025-11-20 12:19:01.876210'),
(56, 'app', '0039_peso_reap', '2025-11-20 12:19:01.954908'),
(57, 'app', '0040_rename_offical_receipt_peso_reap_official_receipt_and_more', '2025-11-20 12:19:02.020707'),
(58, 'app', '0041_rename_released_by_bsrcenter_processed_by_and_more', '2025-11-20 12:19:02.554567'),
(59, 'app', '0042_peso_reap_tracking_number', '2025-11-20 12:19:02.596250'),
(60, 'app', '0043_peso_reap_status', '2025-11-20 12:19:02.646654'),
(61, 'app', '0044_registration_age', '2025-11-20 12:19:02.682708'),
(62, 'app', '0045_registration_zone_street', '2025-11-20 12:19:02.704779'),
(63, 'app', '0046_skills_training_peso_reap_date_claim_expiry_and_more', '2025-11-20 12:19:02.902380'),
(64, 'app', '0047_remove_skills_training_description', '2025-11-20 12:19:02.919946'),
(65, 'app', '0048_year_cycle_alter_customuser_user_type', '2025-11-20 12:19:02.942612'),
(66, 'app', '0049_rename_year_cycle_academic_year_semester', '2025-11-20 12:19:03.007503'),
(67, 'app', '0050_peso_reap_academic_year_peso_reap_semester', '2025-11-20 12:19:03.109861'),
(68, 'app', '0051_user_type_peso_reap_next_registration_user_type', '2025-11-20 12:19:03.215226'),
(69, 'app', '0052_end_user_type_remove_registration_user_type_and_more', '2025-11-20 12:19:03.569238'),
(70, 'app', '0053_rename_sy_end_academic_year_ay_end_and_more', '2025-11-20 12:19:03.606715'),
(71, 'app', '0054_remove_semester_academic_year_academic_year_semester', '2025-11-20 12:19:03.742882'),
(72, 'app', '0055_alter_academic_year_ay_start', '2025-11-20 12:19:03.762756'),
(73, 'app', '0056_remove_peso_reap_semester', '2025-11-20 12:19:03.866104'),
(74, 'app', '0057_remove_peso_reap_date_claim_expiry_and_more', '2025-11-20 12:19:03.926388'),
(75, 'app', '0058_rename_ay_start_academic_year_year_and_more', '2025-11-20 12:19:03.961390'),
(76, 'app', '0059_reap_type_peso_reap_reap_type', '2025-11-20 12:19:04.022304'),
(77, 'app', '0060_occupation_rfidauth_registration_and_more', '2025-11-20 12:19:04.213723'),
(78, 'sessions', '0001_initial', '2025-11-20 12:19:04.241429'),
(79, 'app', '0061_alter_rfidauth_registration', '2025-11-20 12:24:01.537032'),
(80, 'app', '0062_alter_rfidauth_registration', '2025-11-20 12:24:59.215295'),
(81, 'app', '0063_civil_status_remove_registration_civil_status', '2025-11-20 12:48:20.748549'),
(82, 'app', '0064_registration_civil_status', '2025-11-20 12:51:34.476805'),
(83, 'app', '0065_rename_date_claimed_peso_tupad_date_issued_and_more', '2025-11-21 01:03:43.009417'),
(84, 'app', '0066_bsrcenter_actioned_at_bsrcenter_actioned_by_and_more', '2025-11-21 03:30:22.637640');

-- --------------------------------------------------------

--
-- Table structure for table `django_session`
--

CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `app_academic_year`
--
ALTER TABLE `app_academic_year`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `app_academic_year_ay_start_018af980_uniq` (`year`),
  ADD KEY `app_academic_year_semester_id_5ad3a80c_fk_app_semester_id` (`semester_id`);

--
-- Indexes for table `app_barangay`
--
ALTER TABLE `app_barangay`
  ADD PRIMARY KEY (`id`),
  ADD KEY `app_barangay_municipality_id_81dc7311_fk_app_municipality_id` (`municipality_id`);

--
-- Indexes for table `app_bsrcenter`
--
ALTER TABLE `app_bsrcenter`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `tracking_number` (`tracking_number`),
  ADD KEY `app_bsrcenter_registration_id_c77bb837_fk_app_registration_id` (`registration_id`),
  ADD KEY `app_bsrcenter_status_id_f97196c3_fk_app_status_id` (`status_id`),
  ADD KEY `app_bsrcenter_processed_by_id_143fb794_fk_app_customuser_id` (`processed_by_id`),
  ADD KEY `app_bsrcenter_actioned_by_id_400883af_fk_app_customuser_id` (`actioned_by_id`);

--
-- Indexes for table `app_bsrcenter_burial`
--
ALTER TABLE `app_bsrcenter_burial`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `tracking_number` (`tracking_number`),
  ADD KEY `app_bsrcenter_burial_registration_id_712723fe_fk_app_regis` (`registration_id`),
  ADD KEY `app_bsrcenter_burial_status_id_c080c3e1` (`status_id`),
  ADD KEY `app_bsrcenter_burial_processed_by_id_e0ec94e7_fk_app_custo` (`processed_by_id`),
  ADD KEY `app_bsrcenter_burial_actioned_by_id_16fe656c_fk_app_custo` (`actioned_by_id`);

--
-- Indexes for table `app_bsrcenter_meds`
--
ALTER TABLE `app_bsrcenter_meds`
  ADD PRIMARY KEY (`id`),
  ADD KEY `app_bsrcenter_meds_bsrcenter_id_ab8a40b5_fk_app_bsrcenter_id` (`bsrcenter_id`),
  ADD KEY `app_bsrcenter_meds_medicines_id_eff60430_fk_app_medicines_id` (`medicines_id`);

--
-- Indexes for table `app_civil_status`
--
ALTER TABLE `app_civil_status`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `app_customuser`
--
ALTER TABLE `app_customuser`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `app_customuser_groups`
--
ALTER TABLE `app_customuser_groups`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `app_customuser_groups_customuser_id_group_id_a5a0ca22_uniq` (`customuser_id`,`group_id`),
  ADD KEY `app_customuser_groups_group_id_47e49ebd_fk_auth_group_id` (`group_id`);

--
-- Indexes for table `app_customuser_user_permissions`
--
ALTER TABLE `app_customuser_user_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `app_customuser_user_perm_customuser_id_permission_22e31019_uniq` (`customuser_id`,`permission_id`),
  ADD KEY `app_customuser_user__permission_id_c5920c75_fk_auth_perm` (`permission_id`);

--
-- Indexes for table `app_end_user_type`
--
ALTER TABLE `app_end_user_type`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `app_medicines`
--
ALTER TABLE `app_medicines`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `app_municipality`
--
ALTER TABLE `app_municipality`
  ADD PRIMARY KEY (`id`),
  ADD KEY `app_municipality_province_id_055db22d_fk_app_province_id` (`province_id`);

--
-- Indexes for table `app_occupation`
--
ALTER TABLE `app_occupation`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `app_peso_reap`
--
ALTER TABLE `app_peso_reap`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `tracking_number` (`tracking_number`),
  ADD KEY `app_peso_reap_registration_id_ca2f34c8_fk_app_registration_id` (`registration_id`),
  ADD KEY `app_peso_reap_processed_by_id_27421924_fk_app_customuser_id` (`processed_by_id`),
  ADD KEY `app_peso_reap_status_id_4bf71818_fk_app_status_id` (`status_id`),
  ADD KEY `app_peso_reap_Academic_year_id_3fbb2753_fk_app_academic_year_id` (`Academic_year_id`),
  ADD KEY `app_peso_reap_reap_type_id_e6b4203a_fk_app_reap_type_id` (`reap_type_id`),
  ADD KEY `app_peso_reap_actioned_by_id_f1350a13_fk_app_customuser_id` (`actioned_by_id`);

--
-- Indexes for table `app_peso_tupad`
--
ALTER TABLE `app_peso_tupad`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `tracking_number` (`tracking_number`),
  ADD KEY `app_peso_tupad_processed_by_id_39163759_fk_app_customuser_id` (`processed_by_id`),
  ADD KEY `app_peso_tupad_registration_id_cc04d6e8_fk_app_registration_id` (`registration_id`),
  ADD KEY `app_peso_tupad_status_id_42b52704_fk_app_status_id` (`status_id`),
  ADD KEY `app_peso_tupad_skills_training_id_54512e0c_fk_app_skill` (`skills_training_id`),
  ADD KEY `app_peso_tupad_actioned_by_id_41894c17_fk_app_customuser_id` (`actioned_by_id`);

--
-- Indexes for table `app_province`
--
ALTER TABLE `app_province`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `app_reap_type`
--
ALTER TABLE `app_reap_type`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `app_registration`
--
ALTER TABLE `app_registration`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `rfid` (`rfid`),
  ADD UNIQUE KEY `app_registration_email_5e6d7823_uniq` (`email`),
  ADD KEY `app_registration_barangay_id_7cc05d75_fk_app_barangay_id` (`barangay_id`),
  ADD KEY `app_registration_municipality_id_45d6e0cd_fk_app_municipality_id` (`municipality_id`),
  ADD KEY `app_registration_province_id_e0f0e400_fk_app_province_id` (`province_id`),
  ADD KEY `app_registration_end_user_type_id_083218a9_fk_app_end_u` (`end_user_type_id`),
  ADD KEY `app_registration_occupation_id_894bd5d2` (`occupation_id`),
  ADD KEY `app_registration_civil_status_id_100c3ab0_fk_app_civil_status_id` (`civil_status_id`);

--
-- Indexes for table `app_rfidauth`
--
ALTER TABLE `app_rfidauth`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `rfid` (`rfid`),
  ADD KEY `app_rfidauth_registration_id_e5936713_fk_app_registration_id` (`registration_id`);

--
-- Indexes for table `app_semester`
--
ALTER TABLE `app_semester`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `app_skills_training`
--
ALTER TABLE `app_skills_training`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `app_status`
--
ALTER TABLE `app_status`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `auth_group`
--
ALTER TABLE `auth_group`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  ADD KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`);

--
-- Indexes for table `auth_permission`
--
ALTER TABLE `auth_permission`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`);

--
-- Indexes for table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  ADD PRIMARY KEY (`id`),
  ADD KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  ADD KEY `django_admin_log_user_id_c564eba6_fk_app_customuser_id` (`user_id`);

--
-- Indexes for table `django_content_type`
--
ALTER TABLE `django_content_type`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`);

--
-- Indexes for table `django_migrations`
--
ALTER TABLE `django_migrations`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `django_session`
--
ALTER TABLE `django_session`
  ADD PRIMARY KEY (`session_key`),
  ADD KEY `django_session_expire_date_a5c62663` (`expire_date`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `app_academic_year`
--
ALTER TABLE `app_academic_year`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `app_barangay`
--
ALTER TABLE `app_barangay`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT for table `app_bsrcenter`
--
ALTER TABLE `app_bsrcenter`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `app_bsrcenter_burial`
--
ALTER TABLE `app_bsrcenter_burial`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `app_bsrcenter_meds`
--
ALTER TABLE `app_bsrcenter_meds`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `app_civil_status`
--
ALTER TABLE `app_civil_status`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `app_customuser`
--
ALTER TABLE `app_customuser`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `app_customuser_groups`
--
ALTER TABLE `app_customuser_groups`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `app_customuser_user_permissions`
--
ALTER TABLE `app_customuser_user_permissions`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `app_end_user_type`
--
ALTER TABLE `app_end_user_type`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `app_medicines`
--
ALTER TABLE `app_medicines`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `app_municipality`
--
ALTER TABLE `app_municipality`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `app_occupation`
--
ALTER TABLE `app_occupation`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `app_peso_reap`
--
ALTER TABLE `app_peso_reap`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `app_peso_tupad`
--
ALTER TABLE `app_peso_tupad`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `app_province`
--
ALTER TABLE `app_province`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `app_reap_type`
--
ALTER TABLE `app_reap_type`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `app_registration`
--
ALTER TABLE `app_registration`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `app_rfidauth`
--
ALTER TABLE `app_rfidauth`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `app_semester`
--
ALTER TABLE `app_semester`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `app_skills_training`
--
ALTER TABLE `app_skills_training`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `app_status`
--
ALTER TABLE `app_status`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `auth_group`
--
ALTER TABLE `auth_group`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `auth_permission`
--
ALTER TABLE `auth_permission`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=101;

--
-- AUTO_INCREMENT for table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=46;

--
-- AUTO_INCREMENT for table `django_content_type`
--
ALTER TABLE `django_content_type`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=26;

--
-- AUTO_INCREMENT for table `django_migrations`
--
ALTER TABLE `django_migrations`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=85;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `app_academic_year`
--
ALTER TABLE `app_academic_year`
  ADD CONSTRAINT `app_academic_year_semester_id_5ad3a80c_fk_app_semester_id` FOREIGN KEY (`semester_id`) REFERENCES `app_semester` (`id`);

--
-- Constraints for table `app_barangay`
--
ALTER TABLE `app_barangay`
  ADD CONSTRAINT `app_barangay_municipality_id_81dc7311_fk_app_municipality_id` FOREIGN KEY (`municipality_id`) REFERENCES `app_municipality` (`id`);

--
-- Constraints for table `app_bsrcenter`
--
ALTER TABLE `app_bsrcenter`
  ADD CONSTRAINT `app_bsrcenter_actioned_by_id_400883af_fk_app_customuser_id` FOREIGN KEY (`actioned_by_id`) REFERENCES `app_customuser` (`id`),
  ADD CONSTRAINT `app_bsrcenter_processed_by_id_143fb794_fk_app_customuser_id` FOREIGN KEY (`processed_by_id`) REFERENCES `app_customuser` (`id`),
  ADD CONSTRAINT `app_bsrcenter_registration_id_c77bb837_fk_app_registration_id` FOREIGN KEY (`registration_id`) REFERENCES `app_registration` (`id`),
  ADD CONSTRAINT `app_bsrcenter_status_id_f97196c3_fk_app_status_id` FOREIGN KEY (`status_id`) REFERENCES `app_status` (`id`);

--
-- Constraints for table `app_bsrcenter_burial`
--
ALTER TABLE `app_bsrcenter_burial`
  ADD CONSTRAINT `app_bsrcenter_burial_actioned_by_id_16fe656c_fk_app_custo` FOREIGN KEY (`actioned_by_id`) REFERENCES `app_customuser` (`id`),
  ADD CONSTRAINT `app_bsrcenter_burial_processed_by_id_e0ec94e7_fk_app_custo` FOREIGN KEY (`processed_by_id`) REFERENCES `app_customuser` (`id`),
  ADD CONSTRAINT `app_bsrcenter_burial_registration_id_712723fe_fk_app_regis` FOREIGN KEY (`registration_id`) REFERENCES `app_registration` (`id`),
  ADD CONSTRAINT `app_bsrcenter_burial_status_id_c080c3e1_fk_app_status_id` FOREIGN KEY (`status_id`) REFERENCES `app_status` (`id`);

--
-- Constraints for table `app_bsrcenter_meds`
--
ALTER TABLE `app_bsrcenter_meds`
  ADD CONSTRAINT `app_bsrcenter_meds_bsrcenter_id_ab8a40b5_fk_app_bsrcenter_id` FOREIGN KEY (`bsrcenter_id`) REFERENCES `app_bsrcenter` (`id`),
  ADD CONSTRAINT `app_bsrcenter_meds_medicines_id_eff60430_fk_app_medicines_id` FOREIGN KEY (`medicines_id`) REFERENCES `app_medicines` (`id`);

--
-- Constraints for table `app_customuser_groups`
--
ALTER TABLE `app_customuser_groups`
  ADD CONSTRAINT `app_customuser_group_customuser_id_164d073f_fk_app_custo` FOREIGN KEY (`customuser_id`) REFERENCES `app_customuser` (`id`),
  ADD CONSTRAINT `app_customuser_groups_group_id_47e49ebd_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);

--
-- Constraints for table `app_customuser_user_permissions`
--
ALTER TABLE `app_customuser_user_permissions`
  ADD CONSTRAINT `app_customuser_user__customuser_id_4bcbaafb_fk_app_custo` FOREIGN KEY (`customuser_id`) REFERENCES `app_customuser` (`id`),
  ADD CONSTRAINT `app_customuser_user__permission_id_c5920c75_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`);

--
-- Constraints for table `app_municipality`
--
ALTER TABLE `app_municipality`
  ADD CONSTRAINT `app_municipality_province_id_055db22d_fk_app_province_id` FOREIGN KEY (`province_id`) REFERENCES `app_province` (`id`);

--
-- Constraints for table `app_peso_reap`
--
ALTER TABLE `app_peso_reap`
  ADD CONSTRAINT `app_peso_reap_Academic_year_id_3fbb2753_fk_app_academic_year_id` FOREIGN KEY (`Academic_year_id`) REFERENCES `app_academic_year` (`id`),
  ADD CONSTRAINT `app_peso_reap_actioned_by_id_f1350a13_fk_app_customuser_id` FOREIGN KEY (`actioned_by_id`) REFERENCES `app_customuser` (`id`),
  ADD CONSTRAINT `app_peso_reap_processed_by_id_27421924_fk_app_customuser_id` FOREIGN KEY (`processed_by_id`) REFERENCES `app_customuser` (`id`),
  ADD CONSTRAINT `app_peso_reap_reap_type_id_e6b4203a_fk_app_reap_type_id` FOREIGN KEY (`reap_type_id`) REFERENCES `app_reap_type` (`id`),
  ADD CONSTRAINT `app_peso_reap_registration_id_ca2f34c8_fk_app_registration_id` FOREIGN KEY (`registration_id`) REFERENCES `app_registration` (`id`),
  ADD CONSTRAINT `app_peso_reap_status_id_4bf71818_fk_app_status_id` FOREIGN KEY (`status_id`) REFERENCES `app_status` (`id`);

--
-- Constraints for table `app_peso_tupad`
--
ALTER TABLE `app_peso_tupad`
  ADD CONSTRAINT `app_peso_tupad_actioned_by_id_41894c17_fk_app_customuser_id` FOREIGN KEY (`actioned_by_id`) REFERENCES `app_customuser` (`id`),
  ADD CONSTRAINT `app_peso_tupad_processed_by_id_39163759_fk_app_customuser_id` FOREIGN KEY (`processed_by_id`) REFERENCES `app_customuser` (`id`),
  ADD CONSTRAINT `app_peso_tupad_registration_id_cc04d6e8_fk_app_registration_id` FOREIGN KEY (`registration_id`) REFERENCES `app_registration` (`id`),
  ADD CONSTRAINT `app_peso_tupad_skills_training_id_54512e0c_fk_app_skill` FOREIGN KEY (`skills_training_id`) REFERENCES `app_skills_training` (`id`),
  ADD CONSTRAINT `app_peso_tupad_status_id_42b52704_fk_app_status_id` FOREIGN KEY (`status_id`) REFERENCES `app_status` (`id`);

--
-- Constraints for table `app_registration`
--
ALTER TABLE `app_registration`
  ADD CONSTRAINT `app_registration_barangay_id_7cc05d75_fk_app_barangay_id` FOREIGN KEY (`barangay_id`) REFERENCES `app_barangay` (`id`),
  ADD CONSTRAINT `app_registration_civil_status_id_100c3ab0_fk_app_civil_status_id` FOREIGN KEY (`civil_status_id`) REFERENCES `app_civil_status` (`id`),
  ADD CONSTRAINT `app_registration_end_user_type_id_083218a9_fk_app_end_u` FOREIGN KEY (`end_user_type_id`) REFERENCES `app_end_user_type` (`id`),
  ADD CONSTRAINT `app_registration_municipality_id_45d6e0cd_fk_app_municipality_id` FOREIGN KEY (`municipality_id`) REFERENCES `app_municipality` (`id`),
  ADD CONSTRAINT `app_registration_occupation_id_894bd5d2_fk_app_occupation_id` FOREIGN KEY (`occupation_id`) REFERENCES `app_occupation` (`id`),
  ADD CONSTRAINT `app_registration_province_id_e0f0e400_fk_app_province_id` FOREIGN KEY (`province_id`) REFERENCES `app_province` (`id`);

--
-- Constraints for table `app_rfidauth`
--
ALTER TABLE `app_rfidauth`
  ADD CONSTRAINT `app_rfidauth_registration_id_e5936713_fk_app_registration_id` FOREIGN KEY (`registration_id`) REFERENCES `app_registration` (`id`);

--
-- Constraints for table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  ADD CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  ADD CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);

--
-- Constraints for table `auth_permission`
--
ALTER TABLE `auth_permission`
  ADD CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);

--
-- Constraints for table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  ADD CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  ADD CONSTRAINT `django_admin_log_user_id_c564eba6_fk_app_customuser_id` FOREIGN KEY (`user_id`) REFERENCES `app_customuser` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
