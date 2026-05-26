# Load the necessary libraries
library(readxl)
library(dplyr)
library(psych)
options(scipen=999)


file_path <- "Enter your file path here"
data <- read_excel(file_path)
data<-data[data$`filter_$`==1,]


#statistics
mean(data$age.0)
sd(data$age.0)

gender_counts <- table(data$Gender)
gender_proportions <- prop.table(gender_counts)
(gender_percentages <- gender_proportions * 100)

summary(data$SC0)
sd(data$SC0)

####################
# Tasks mean
####################


# Calculate Cronbach's alpha for the 5 tasks
# Select columns that start with "tasks_"
tasks_columns <- grep("^tasks_", names(data), value = TRUE)
cronbach_alpha_result <- psych::alpha(data[, tasks_columns])
# Print the result
cronbach_alpha_result$total$raw_alpha #.7777




# Fit the model
model <- lm(Tasks ~ SC0, data = data)

# Print summary
summary(model)

confint(model)


# Fit the model with controls
data$Gender_fac<-as.factor(data$Gender)
data$Income_fac<-as.factor(data$hhi)

model_controls <- lm(Tasks ~ SC0+Age+Gender_fac+Income_fac, data = data)

# Print summary
summary(model_controls)

confint(model_controls)

####################
# magicalness mean
####################

# Calculate Cronbach's alpha for the 5 tasks
# Select columns that start with "Q" but not Q70 (the attention check)
magical_columns <- grep("^Q(?!70$)", names(data), value = TRUE, perl = TRUE)
cronbach_alpha_result <- psych::alpha(data[, magical_columns])
# Print the result
cronbach_alpha_result$total$raw_alpha #.8562


# Fit the model
model2 <- lm(MagicalPerceptions ~ SC0, data = data)

# Print summary
summary(model2)

confint(model2)


# model with controls

# Fit the model
model2_controls <- lm(MagicalPerceptions ~ SC0+Age+Gender_fac+Income_fac, data = data)

# Print summary
summary(model2_controls)

confint(model2_controls)

######################
# mediation check
#######################

library(mediation)

# Fit the mediator model
mediator_model <- lm(MagicalPerceptions ~ SC0, data = data)

# Fit the outcome model
outcome_model <- lm(Tasks ~ MagicalPerceptions + SC0, data = data)

# Conduct the mediation analysis
med_out <- mediate(mediator_model, outcome_model, treat = 'SC0', mediator = 'MagicalPerceptions',
                   boot = TRUE, sims = 10000)

# Print the result
summary(med_out)

