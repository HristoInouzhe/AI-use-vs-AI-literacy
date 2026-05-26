# Load the necessary libraries
library(readxl)
library(dplyr)
library(psych)
options(scipen=999)


file_path <- "Enter your file path here"

data <- read_excel(file_path)
data<-data[data$`filter_$`==1,]
#remove another person that answered IMC correct but dropped
data<-data[!is.na(data$AIScore),]


#statistics
data$age.0<-as.numeric(data$age.0)
mean(data$age.0)
sd(data$age.0)

data$Gender<-as.numeric(data$Gender)
gender_counts <- table(data$Gender)
gender_proportions <- prop.table(gender_counts)
(gender_percentages <- gender_proportions * 100)

summary(data$AIScore)
sd(data$AIScore)

####################
# Receptivity
####################
# Fit the model with interaction
model1 <- lm(DV ~ AIScore_centered, data = data)

# Print summary
summary(model1)

confint(model1)


# Fit the model with interaction
model2 <- lm(DV ~ AIScore_centered*cond, data = data)

# Print summary
summary(model2)

confint(model2)

# checking for correlation, removing one person from each group that did not answer the DV
cor.test(data$AIScore_centered[data$cond=="magical"&!is.na(data$DV)],data$DV[data$cond=="magical"&!is.na(data$DV)])
cor.test(data$AIScore_centered[data$cond=="capable"&!is.na(data$DV)],data$DV[data$cond=="capable"&!is.na(data$DV)])
