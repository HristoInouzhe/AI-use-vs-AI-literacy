# Load necessary library
library(readxl)
library(dplyr)
library(psych)
library(tidyr)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
options(scipen=999)

file_path <- "Enter your file path here"
file_path2 <- "Enter your file path here"


# Read the Excel file
data <- read_excel(file_path)

#filter out those that did not pass the inclusion criteria
data<-data[data$`filter_$`==1,]
# View the first few rows of the data frame
head(data)


# Read the Excel file for subjectivity measures
objdata <- read_excel(file_path2)

# View the first few rows of the data frame
head(objdata)

summary(data$Age)
sd(data$Age)

gender_counts <- table(data$Gender)
gender_proportions <- prop.table(gender_counts)
(gender_percentages <- gender_proportions * 100)

summary(data$AILTScore)
sd(data$AILTScore)

# Calculate Cronbach's alpha for the 26 tasks
# Select columns that start with "tasks_"
tasks_columns <- grep("^tasks_", names(data), value = TRUE)
cronbach_alpha_result <- psych::alpha(data[, tasks_columns])
# Print the result
cronbach_alpha_result$total$raw_alpha #.9185



# regression of AI Receptivity on AI Literacy

# Mean center AI literacy measure
data$MC_AILT<-data$AILTScore-mean(data$AILTScore)


model1 <- lm(taskOverall ~ AILTScore, data=data)

# Get the summary of the model
summary(model1)
confint(model1)

# model 1 with controls
data$Gender_fac<-as.factor(data$Gender)
data$Income_fac<-as.factor(data$Income)

model1_controls <- lm(taskOverall ~ AILTScore+Gender_fac+Income_fac+Age, data=data)

# Get the summary of the model
summary(model1_controls)
confint(model1_controls)

# checking for square root transformation
data$AILTScoresqrt<-sqrt(data$AILTScore)
model1sqrt <- lm(taskOverall ~ AILTScoresqrt, data=data)

# Get the summary of the model
summary(model1sqrt)
confint(model1sqrt)


# Run the linear model 
model2 <- lm(taskOverall ~ AILTScore*order, data=data)

# Get the summary of the model
summary(model2)
confint(model2)



# Run the linear model with controls
model2_controls <- lm(taskOverall ~ AILTScore*order+Gender_fac+Income_fac+Age, data=data)

# Get the summary of the model
summary(model2_controls)
confint(model2_controls)

# checking for square root transformation
model2sqrt <- lm(taskOverall ~ AILTScoresqrt*order, data=data)

# Get the summary of the model
summary(model2sqrt)
confint(model2sqrt)

##################################
# Subjectivity analysis
#############################


# Filter the dataset for rows where 'filter_$' is 1
filtered_data <- objdata %>% 
  filter(`filter_$` == 1)

# Calculate the mean for each task column in the filtered dataset
task_means <- filtered_data %>%
  select(starts_with("tasks_")) %>%
  summarise(across(everything(), ~ mean(.x, na.rm = TRUE)))

# Convert the summary to a named vector
mean_vector <- as.vector(unlist(task_means))
names(mean_vector) <- names(task_means)

# Calculate the mean of all task averages
mean_of_means <- mean(mean_vector)

# Create a data frame with task name, task average, and mean-centered values
mean_centered_df <- data.frame(
  task_name = names(mean_vector),
  task_average = mean_vector,
  mean_centered = mean_vector - mean_of_means
)

# Add an ID column
data <- data %>%
  mutate(ID = row_number())

# Convert 'data' to long format, keeping specified fields
long_data <- data %>%
  pivot_longer(
    cols = starts_with("tasks_"),
    names_to = "Task",
    values_to = "Task_Value"
  ) %>%
  select(ID, Task, Task_Value, religion_1, Gender, Age, Income, AILTScore,MC_AILT, order, taskOverall, AILTScoresqrt,Gender_fac,Income_fac)

# Prepare mean_centered_df for joining by ensuring column names match
# Here we assume mean_centered_df has 'task_name' and 'mean_centered' among other columns
mean_centered_df <- mean_centered_df %>%
  rename(Task = task_name)
mean_centered_df <- mean_centered_df %>%
  rename(MC_Obj = mean_centered)


# Merge the mean-centered values into the long format data
long_data_with_mean_centered <- long_data %>%
  left_join(mean_centered_df, by = "Task")

# View the result to confirm the merge
print(head(long_data_with_mean_centered))



library(lme4)
library(lmerTest)


# Recode ID variable to factor
long_data_with_mean_centered$ID <- factor(long_data_with_mean_centered$ID)

# Run mixed-effects model
model3 <- lmer(Task_Value ~ MC_AILT *MC_Obj+ (1 | ID), data = long_data_with_mean_centered, REML = TRUE)

# Print summary
summary(model3)
confint(model3)



# Run mixed-effects model with controls
model3_controls <- lmer(Task_Value ~ MC_AILT *MC_Obj+Gender_fac+Income_fac+Age+ (1 | ID), data = long_data_with_mean_centered, REML = TRUE)

# Print summary
summary(model3_controls)
confint(model3_controls)

# check model with square root AILTScore
# Run mixed-effects model
model3sqrt <- lmer(Task_Value ~ AILTScoresqrt *MC_Obj+ (1 | ID), data = long_data_with_mean_centered, REML = TRUE)
summary(model3sqrt)
