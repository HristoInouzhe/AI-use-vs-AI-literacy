library(readxl)
options(scipen=999)
file_path <- "Enter your file path here"
# Read the Excel file
data <- read_excel(file_path)
data<-data[data$`filter_$`==1,]

# View the first few rows of the data frame
head(data)

summary(data$SC0)
sd(data$SC0)



library(psych)

# Calculate Cronbach's alpha for the five products and services
cronbach_alpha_result <- psych::alpha(data[, c(6:10)])

# Print the result
cronbach_alpha_result$total$raw_alpha #.743

# regression of AI Receptivity on AI Literacy
model1 <- lm(Usage ~ AIScore, data=data)

# Get the summary of the model
summary(model1)
confint(model1)


# regression of AI Receptivity on AI Literacy with controls
data$Income_fac<-as.factor(data$Income)
data$Gender_fac<-as.factor(data$Gender)

model1_controls <- lm(Usage ~ AIScore+Age+Gender_fac+Income_fac, data=data)

# Get the summary of the model
summary(model1_controls)
confint(model1_controls)



# AI Literacy and Age
(cor_test_ai_age <- cor.test(data$AIScore, data$Age, method = "pearson"))

# AI Literacy and Income
(cor_test_ai_income <- cor.test(data$AIScore, data$Income, method = "pearson"))

# AI Literacy and TRI
(cor_test_ai_tri <- cor.test(data$AIScore, data$TRI, method = "pearson"))

# AI Literacy and autonomy
(cor_test_ai_autonomy <- cor.test(data$AIScore, data$Autonomy, method = "pearson"))

# AI Literacy and General knowledge
(cor_test_ai_GenKno <- cor.test(data$AIScore, data$GenKnow, method = "pearson"))

# AI Literacy and Male
(cor_test_ai_male <- cor.test(data$AIScore, data$Gender_dummy_1, method = "pearson"))

# AI usage and TRI
(cor_test_usage_tri <- cor.test(data$Usage, data$TRI, method = "pearson"))

# AI usage and male
(cor_test_usage_male <- cor.test(data$Usage, data$Gender_dummy_1, method = "pearson"))

# AI usage and autonomy
(cor_test_usage_autonomy <- cor.test(data$Usage, data$Autonomy, method = "pearson"))

# AI usage and General knowledge
(cor_test_usage_GenKno <- cor.test(data$Usage, data$GenKnow, method = "pearson"))


# Run the linear model
model2 <- lm(Usage ~ AIScore+TRI+GenKnow+Autonomy+Gender_dummy_1, data=data)

# Get the summary of the model
summary(model2)
confint(model2)

library(stargazer)
stargazer(model1, model2, type = "text")


# Run the linear model with full controls
model2_controls <- lm(Usage ~ AIScore+TRI+GenKnow+Autonomy+Gender_fac+Age+Income_fac, data=data)

# Get the summary of the model
summary(model2_controls)
confint(model2_controls)


#sq root transform

model1sq <- lm(Usage ~ sqrtAIScore, data=data)

# Get the summary of the model
summary(model1sq)
confint(model1sq)

model2sq <- lm(Usage ~ sqrtAIScore+TRI+GenKnow+Autonomy+Gender_dummy_1, data=data)

# Get the summary of the model
summary(model2sq)
confint(model2sq)
stargazer(model1sq, model2sq, type = "text")



# only negatively covatiates

model2neg <- lm(Usage ~ AIScore+GenKnow+Autonomy, data=data)

# Get the summary of the model
summary(model2neg)
confint(model2neg)

# full demographics

model2full <- lm(Usage ~ AIScore+TRI+GenKnow+Autonomy+Gender_dummy_1+Income+Age, data=data)

# Get the summary of the model
summary(model2full)
confint(model2full)

stargazer(model1, model2,model2neg, model2full, type = "text")

# only variables with full observations (remove 22 with NA in TRI)

# Run the linear model
model2 <- lm(Usage ~ AIScore, data=data[!is.na(data$TRI),])

# Get the summary of the model
summary(model2)
confint(model2)
