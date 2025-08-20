-- CreateEnum
CREATE TYPE "ReportStatus" AS ENUM ('PENDING', 'FAILED', 'SUCCESSFUL');

-- CreateTable
CREATE TABLE "Reports" (
    "id" TEXT NOT NULL,
    "storeId" TEXT NOT NULL,
    "status" "ReportStatus" NOT NULL DEFAULT 'PENDING',
    "report" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updateAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Reports_pkey" PRIMARY KEY ("id")
);
