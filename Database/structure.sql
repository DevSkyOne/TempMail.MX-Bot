
create table if not exists
  `discord_emails` (
    `clientid` varchar(255) not null,
    `mail` VARCHAR(255) not null,
    `latest_usage` TIMESTAMP not null default CURRENT_TIMESTAMP,
    `created_at` timestamp not null default CURRENT_TIMESTAMP,
    primary key (`clientid`, `mail`)
  ) engine=InnoDB default charset=utf8mb4;