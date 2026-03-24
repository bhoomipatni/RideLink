CREATE TABLE "Users"(
    "username" VARCHAR(255) NOT NULL,
    "email" VARCHAR(255) NOT NULL,
    "rcsid" VARCHAR(255) NOT NULL,
    "isdriver" BOOLEAN NOT NULL,
    "password" VARCHAR(255) NOT NULL
    "rides" INT[] NOT NULL
);
CREATE INDEX "users_id_username_rcsid_index" ON
    "Users"("username", "rcsid");
ALTER TABLE
    "Users" ADD CONSTRAINT "users_username_unique" UNIQUE("username");
ALTER TABLE
    "Users" ADD CONSTRAINT "users_email_unique" UNIQUE("email");
ALTER TABLE
    "Users" ADD CONSTRAINT "users_rcsid_unique" UNIQUE("rcsid");
CREATE TABLE "Rides"(
    "id" SERIAL NOT NULL,
    "date" DATE NOT NULL,
    "driverid" BIGINT NOT NULL,
    "orgin" VARCHAR(255) NOT NULL,
    "address" VARCHAR(255) NOT NULL,
    "cost" FLOAT(53) NOT NULL,
    "isactive" BOOLEAN NOT NULL,
    "description" VARCHAR(255) NOT NULL,
    "lat" FLOAT(53) NOT NULL,
    "long" FLOAT(53) NOT NULL,
    "riders" INT[] NOT NULL
);
ALTER TABLE
    "Rides" ADD CONSTRAINT "rides_id_unique" UNIQUE("id");